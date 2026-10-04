import sqlite3
from Utilis.Validator import Validator
from datetime import datetime, timedelta


class StudentRepo:
    def __init__(self, db_name: str):
        self.db_name = db_name


    def get_student(self, telegr_id: int):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query = cursor.execute("Select * from students_accounts where telegr_id = ?", (telegr_id,))
            return query.fetchone()

    def add_student(self,values: dict):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query_students = cursor.execute("INSERT INTO students(name,phone_number, email) VALUES(?,?,?)",(values.get("name"), values.get("phone_number"), values.get("email")))
            student_id = cursor.lastrowid
            hash = Validator.make_hash(values.get("password"))
            query_students_accounts = cursor.execute("INSERT INTO students_accounts(telegr_id,for_student,login, password_hash,last_time_online) VALUES(?,?,?,?,?)",(values.get("telegr_id"),student_id,values.get("nickname"), hash, datetime.now()))


    def check_if_logged(self,telegr_id: int):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query = cursor.execute("Select is_loged from students_accounts where telegr_id = ?", (telegr_id,))
            result = query.fetchone()[0]
            return result

    def show_profile_data(self, telegr_id: int):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query = cursor.execute("Select s.name, s.phone_number, s.email, sa.last_time_online, sa.balance from students_accounts sa, students s where telegr_id = ? and  sa.for_student = s.student_id", (telegr_id,))
            return query.fetchone()

    def logout_inactive_users(self):
        threshold = (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE students_accounts
                SET is_loged = 0
                WHERE last_time_online <= ?
                AND is_loged = 1
            """, (threshold,))

    def update_activity(self, telegram_id: int):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE students_accounts
                SET last_time_online = ?, is_loged = 1
                WHERE telegr_id = ?
            """, (now, telegram_id))
            conn.commit()

    def get_hash(self, telegram_id: int):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query = cursor.execute("""
                SELECT password_hash from students_accounts
                WHERE telegr_id = ?
            """,(telegram_id,))
            return query.fetchone()

    def login_user(self, telegram_id: int):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query = cursor.execute("""
                UPDATE students_accounts
                SET is_loged = 1
                WHERE telegr_id = ?
            """, (telegram_id,))

    def delete_user_info(self, telegram_id: int) -> bool:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            try:
                # 1. Знаходимо внутрішній student_id
                cursor.execute(
                    """
                    SELECT sa.for_student
                    FROM students_accounts AS sa
                    WHERE sa.telegr_id = ?
                    """,
                    (telegram_id,)
                )

                student_row = cursor.fetchone()

                if student_row is None:
                    raise ValueError("Акаунт користувача не знайдено")

                student_id = student_row[0]

                # 2. Спочатку отримуємо слоти користувача
                cursor.execute(
                    """
                    SELECT id_of_slot
                    FROM requiring_slots_students
                    WHERE student_id = ?
                    """,
                    (telegram_id,)
                )

                slot_ids = [
                    row[0]
                    for row in cursor.fetchall()
                ]

                # 3. Звільняємо слоти
                for slot_id in slot_ids:
                    cursor.execute(
                        """
                        UPDATE requiring_slots
                        SET status = 'free'
                        WHERE id = ?
                        """,
                        (slot_id,)
                    )

                # 4. Видаляємо запити на перенесення уроків
                cursor.execute(
                    """
                    DELETE FROM resheduled_lessons
                    WHERE lesson_id IN (
                        SELECT lesson_id
                        FROM lessons
                        WHERE account_id = ?
                    )
                    """,
                    (telegram_id,)
                )

                # 5. Видаляємо запити на скасування уроків
                cursor.execute(
                    """
                    DELETE FROM cancelled_lessons
                    WHERE lesson_id IN (
                        SELECT lesson_id
                        FROM lessons
                        WHERE account_id = ?
                    )
                    """,
                    (telegram_id,)
                )

                # 6. Видаляємо всі уроки користувача
                cursor.execute(
                    """
                    DELETE FROM lessons
                    WHERE account_id = ?
                    """,
                    (telegram_id,)
                )

                # 7. Видаляємо зв'язки користувача зі слотами
                cursor.execute(
                    """
                    DELETE FROM requiring_slots_students
                    WHERE student_id = ?
                    """,
                    (telegram_id,)
                )

                # 8. Видаляємо акаунт
                cursor.execute(
                    """
                    DELETE FROM students_accounts
                    WHERE telegr_id = ?
                    """,
                    (telegram_id,)
                )

                # 9. Видаляємо персональні дані студента
                cursor.execute(
                    """
                    DELETE FROM students
                    WHERE student_id = ?
                    """,
                    (student_id,)
                )

                conn.commit()
                return True

            except (sqlite3.Error, ValueError) as error:
                conn.rollback()
                print(f"Помилка видалення акаунту: {error}")
                return False



    def change_profile_data(self, user_id: int, column: str, data: str):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute(f"""
            UPDATE students_accounts
            SET {column} = ?
            WHERE telegr_id = ?
            """, (data, user_id,))

            return cursor.rowcount > 0

    def change_name_profile(self,user_id, new_name: str):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute("""
            SELECT s.student_id from students s, students_accounts sa
            WHERE s.student_id = sa.for_student 
            AND sa.telegr_id = ?
            """, (user_id,))

            student_id = cursor.fetchone()[0]

            cursor = conn.execute("""
            UPDATE students
            SET name = ?
            WHERE student_id = ?
            """, (new_name, student_id))

            return cursor.rowcount > 0


    def create_password_change_request(
            self,
            telegram_id: int,
            new_password: str
    ) -> int | None:
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT 1
                    FROM students_accounts
                    WHERE telegr_id = ?
                    """,
                    (telegram_id,)
                )

                if cursor.fetchone() is None:
                    return None

                cursor.execute(
                    """
                    SELECT request_id
                    FROM password_change_requests
                    WHERE telegram_id = ?
                      AND status = 'pending'
                    """,
                    (telegram_id,)
                )

                existing_request = cursor.fetchone()

                if existing_request is not None:
                    return existing_request[0]

                cursor.execute(
                    """
                    INSERT INTO password_change_requests (
                        telegram_id,
                        new_password
                    )
                    VALUES (?, ?)
                    """,
                    (telegram_id, new_password)
                )

                conn.commit()
                return cursor.lastrowid

        except sqlite3.Error as error:
            print(
                f"Помилка створення запиту "
                f"на зміну пароля: {error}"
            )
            return None

    def accept_password_change(
            self,
            request_id: int
    ) -> int | None:
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT telegram_id, new_password
                    FROM password_change_requests
                    WHERE request_id = ?
                      AND status = 'pending'
                    """,
                    (request_id,)
                )

                request = cursor.fetchone()

                if request is None:
                    return None

                telegram_id = request[0]
                new_password = request[1]

                cursor.execute(
                    """
                    UPDATE students_accounts
                    SET password_hash = ?
                    WHERE telegr_id = ?
                    """,
                    (new_password, telegram_id)
                )

                if cursor.rowcount == 0:
                    raise ValueError(
                        "Акаунт користувача не знайдено"
                    )

                cursor.execute(
                    """
                    UPDATE password_change_requests
                    SET status = 'accepted',
                        processed_at = CURRENT_TIMESTAMP
                    WHERE request_id = ?
                      AND status = 'pending'
                    """,
                    (request_id,)
                )

                conn.commit()
                return telegram_id

        except (sqlite3.Error, ValueError) as error:
            print(
                f"Помилка підтвердження зміни пароля: "
                f"{error}"
            )
            return None

    def reject_password_change(
            self,
            request_id: int
    ) -> int | None:
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT telegram_id
                    FROM password_change_requests
                    WHERE request_id = ?
                      AND status = 'pending'
                    """,
                    (request_id,)
                )

                request = cursor.fetchone()

                if request is None:
                    return None

                telegram_id = request[0]

                cursor.execute(
                    """
                    UPDATE password_change_requests
                    SET status = 'rejected',
                        processed_at = CURRENT_TIMESTAMP
                    WHERE request_id = ?
                      AND status = 'pending'
                    """,
                    (request_id,)
                )

                conn.commit()
                return telegram_id

        except sqlite3.Error as error:
            print(
                f"Помилка відхилення запиту: {error}"
            )
            return None


    def pending_payment(self,student_id: int, amount: int):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                now = datetime.now()
                payed_at = now.strftime("%d.%m.%Y o %H:%M")
                cursor.execute("""
                INSERT INTO payments(payed_by,amount,payed_at,status)
                VALUES(?,?,?,?)
                """, (student_id,amount,payed_at,"pending"))
                return True
        except sqlite3.Error as error:
            print(f"Помилка {error}")
            return False


    def change_status_of_payment(self, payment_id, status: str):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                UPDATE payments
                SET status = ?
                WHERE payment_id = ?
                """,(status,payment_id))

                return cursor.rowcount > 0

        except sqlite3.Error as error:
            print(f"Помилка: {error}")
            return False
    def show_pending_payments(self,student_id):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                pendings = cursor.execute("""
                SELECT * from payments
                WHERE payed_by = ?
                AND status = 'pending'
                """, (student_id,)).fetchall()

                return pendings

        except sqlite3.Error as error:
            print(f"Помилка: {error}")
            return False

    def adding_payment(self,student_id, sum: int):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                old_sum_payment = cursor.execute("""
                SELECT balance from students_accounts
                WHERE telegr_id = ?
                """, (student_id,)).fetchone()[0]

                new_balance = old_sum_payment + sum

                cursor.execute(f"""
                UPDATE students_accounts
                SET balance = {new_balance}
                WHERE telegr_id = ?
                """, (student_id,))

            return True

        except sqlite3.Error as error:
            print(f"Помилка: {error} ")
            return False


    def pay_for_lesson(self, lessons_to_pay: list[int], sum_to_pay: int, telegram_id: int):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                for lesson_id in lessons_to_pay:

                    cursor.execute("""
                    UPDATE lessons
                    SET is_paid = ?
                    WHERE lesson_id = ?
                    """, (1,lesson_id))


                old_balance = cursor.execute("""
                SELECT balance from students_accounts
                WHERE telegr_id = ?
                """, (telegram_id,)).fetchone()[0]

                new_balance = old_balance - sum_to_pay

                if new_balance > 0:
                    cursor.execute("""
                    UPDATE students_accounts
                    SET balance = ?
                    WHERE telegr_id = ?
                    """,(new_balance, telegram_id))
                    return True

                else:
                    print("Недостатньо грошей")
                    conn.rollback()
                    return False

        except sqlite3.Error as error:
            print(f"Проблема в pay_for_lesson: {error}")
            conn.rollback()

    def show_students(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                Select sa.telegr_id, s.name, sa.login from students_accounts sa 
                JOIN students s 
                ON sa.for_student = s.student_id
                """)

                return cursor.fetchall()

        except Exception as e:
            print(f"Помилка: {e}")
            return False

    def get_student_infor_for_admin(self, telegram_id: int):
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                SELECT s.name, sa.login, sa.balance,
                (
                    Select COUNT(*)
                    FROM lessons l JOIN students_accounts sa ON l.account_id = sa.telegr_id
                    AND l.status IN ('active', 'active_onetime_lesson')
                    AND l.is_in_past = 1
                ) as completed_lesson,
                
                (
                SELECT COUNT(*)
                FROM lessons l
                WHERE l.account_id = sa.telegr_id
                AND l.is_paid = 0
                AND is_in_past = 0
                ) AS unpaid_lessons,
                
                (
                SELECT COUNT(*)
                FROM lessons l
                WHERE l.account_id = sa.telegr_id
                AND l.status = 'canceled'
                ) AS canceled_lessons,
                
                (
                SELECT MIN(l.start_time)
                FROM lessons l
                WHERE l.account_id = sa.telegr_id
                        AND l.start_time > datetime('now')
                        AND l.status = 'active'
                ) AS next_lesson
                
                FROM students s
                JOIN students_accounts sa
                    ON sa.for_student = s.student_id

                WHERE sa.telegr_id = ?
                """, (telegram_id,))

                student = cursor.fetchone()

                if student is None:
                    return None

                return dict(student)

        except sqlite3.Error as e:
            print(f"Помилка отримання інформації про учня: {e}")
            return None






