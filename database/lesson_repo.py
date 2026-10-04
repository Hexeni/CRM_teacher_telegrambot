import sqlite3
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo


class LessonRepo:
    def __init__(self, db_name):
        self.db_name = db_name

    def show_lessons(self, telegram_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query = cursor.execute("""
            SELECT l.lesson_id, l.start_time, l.is_paid, l.status from lessons l, students_accounts sa 
            WHERE sa.telegr_id = l.lesson_id
            """)
            if query.fetchone():
                return query.fetchone()
            else:
                return 0

    def show_slots(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query = cursor.execute("""
            SELECT * FROM requiring_slots
            """)
            return query.fetchall()

    def show_slot(self, slot_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query = cursor.execute("""
            SELECT * from requiring_slots where id = ?
            """, (slot_id,))
            return query.fetchone()

    def show_free_slots(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query = cursor.execute("""
            SELECT * from requiring_slots 
            WHERE status = 'free'
            """)
            return query.fetchall()

    def show_slots_for_students(self, student_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            query = cursor.execute("""
                SELECT
                    rs.id,
                    rs.weekday,
                    rs.time_for_slot
                FROM requiring_slots rs
                JOIN requiring_slots_students rss
                    ON rss.id_of_slot = rs.id
                WHERE rss.student_id = ?
            """, (student_id,))

            return query.fetchall()

    def update_slot_for_student(
            self,
            old_slot_id: int,
            new_slot_id: int,
            student_id: int
    ) -> bool:

        with sqlite3.connect(self.db_name) as conn:
            try:
                cursor = conn.cursor()

                # 1. Отримуємо дані нового слота
                cursor.execute(
                    """
                    SELECT
                        status,
                        weekday,
                        time_for_slot,
                        duration_minutes
                    FROM requiring_slots
                    WHERE id = ?
                    """,
                    (new_slot_id,)
                )

                new_slot = cursor.fetchone()

                if new_slot is None:
                    raise ValueError("Новий слот не знайдено")

                status, weekday, time_for_slot, duration_minutes = new_slot

                if status != "free":
                    raise ValueError("Новий слот уже зайнятий")

                # 2. Перевіряємо, чи старий слот належить учню
                cursor.execute(
                    """
                    SELECT 1
                    FROM requiring_slots_students
                    WHERE id_of_slot = ?
                      AND student_id = ?
                    """,
                    (old_slot_id, student_id)
                )

                if cursor.fetchone() is None:
                    raise ValueError("Цей слот не належить учню")

                # 3. Видаляємо майбутні уроки старого слота
                cursor.execute(
                    """
                    DELETE FROM lessons
                    WHERE slot_id = ?
                      AND account_id = ?
                      AND is_in_past = 0
                    """,
                    (old_slot_id, student_id)
                )

                # 4. Старий слот знову стає вільним
                cursor.execute(
                    """
                    UPDATE requiring_slots
                    SET status = 'free'
                    WHERE id = ?
                    """,
                    (old_slot_id,)
                )

                # 5. Замінюємо слот учня
                cursor.execute(
                    """
                    UPDATE requiring_slots_students
                    SET id_of_slot = ?
                    WHERE id_of_slot = ?
                      AND student_id = ?
                    """,
                    (new_slot_id, old_slot_id, student_id)
                )

                if cursor.rowcount == 0:
                    raise ValueError("Не вдалося змінити слот учня")

                # 6. Новий слот стає зайнятим
                cursor.execute(
                    """
                    UPDATE requiring_slots
                    SET status = 'reserved'
                    WHERE id = ?
                      AND status = 'free'
                    """,
                    (new_slot_id,)
                )

                if cursor.rowcount == 0:
                    raise ValueError("Новий слот уже зайнятий")

                # 7. Обчислюємо дату першого уроку
                now = datetime.now()


                python_weekday = weekday - 1

                time_parts = time_for_slot.split(":")

                hour = int(time_parts[0])
                minute = int(time_parts[1])

                second = 0

                if len(time_parts) >= 3:
                    second = int(time_parts[2])

                days_until_lesson = (
                                            python_weekday - now.weekday()
                                    ) % 7

                datetime_of_begining = now.replace(
                    hour=hour,
                    minute=minute,
                    second=second,
                    microsecond=0
                ) + timedelta(days=days_until_lesson)

                # Якщо сьогоднішній час уже минув,
                # перший урок буде наступного тижня
                if datetime_of_begining <= now:
                    datetime_of_begining += timedelta(weeks=1)

                datetime_of_ending = (
                        datetime_of_begining
                        + timedelta(minutes=duration_minutes)
                )

                # 8. Створюємо 4 уроки нового слота
                for week in range(4):
                    week_shift = timedelta(weeks=week)

                    start_time = datetime_of_begining + week_shift
                    end_time = datetime_of_ending + week_shift

                    cursor.execute(
                        """
                        INSERT INTO lessons (
                            slot_id,
                            account_id,
                            start_time,
                            end_time
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            new_slot_id,
                            student_id,
                            start_time.isoformat(sep=" "),
                            end_time.isoformat(sep=" ")
                        )
                    )

                # Commit лише після успішного виконання всіх дій
                conn.commit()

                return True

            except (
                    sqlite3.Error,
                    ValueError,
                    TypeError
            ) as error:
                conn.rollback()

                print(f"Помилка під час зміни слота: {error}")

                return False




    def approve_slot_and_create_lesson(self, slot_id, student_id, datetime_of_begining, datetime_of_ending):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO requiring_slots_students (id_of_slot, student_id)
                    VALUES (?, ?)
                    """,
                    (slot_id, student_id)
                )

                cursor.execute(
                    """
                    UPDATE requiring_slots
                    SET status = 'reserved'
                    WHERE id = ?  
                    """,
                    (slot_id,)
                )

                days_ahead = 0
                for x in range(4):
                    cursor.execute(
                        """
                        INSERT INTO lessons (slot_id, account_id, start_time, end_time)
                        VALUES (?, ?, ?, ?)
                        """,
                        (slot_id, student_id, str(datetime_of_begining + timedelta(days_ahead)),
                         str(datetime_of_ending + timedelta(days_ahead)))
                    )
                    days_ahead += 7

                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def adding_new_lessons_automatically(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            try:
                now = datetime.now().isoformat(sep=' ')

                # 1. Позначаємо старі уроки як минулі
                cursor.execute("""
                    UPDATE lessons
                    SET is_in_past = 1
                    WHERE is_in_past = 0
                      AND end_time < ?
                """, (now,))

                # 2. Беремо всі пари студент + слот
                pairs = cursor.execute("""
                    SELECT student_id, id_of_slot
                    FROM requiring_slots_students
                """).fetchall()

                for student_id, slot_id in pairs:
                    # 3. Рахуємо, скільки ще є майбутніх/активних уроків
                    active_count = cursor.execute("""
                        SELECT COUNT(*)
                        FROM lessons
                        WHERE account_id = ?
                          AND slot_id = ?
                          AND is_in_past = 0
                          AND status != 'rescheduled'
                    """, (student_id, slot_id)).fetchone()[0]

                    # Якщо вже є 4 або більше - нічого не робимо
                    if active_count >= 4:
                        continue

                    # 4. Знаходимо останній урок по цьому слоту і студенту
                    last_lesson = cursor.execute("""
                        SELECT start_time, end_time
                        FROM lessons
                        WHERE account_id = ?
                          AND slot_id = ?
                          AND status != 'rescheduled'
                        ORDER BY start_time DESC
                        LIMIT 1
                    """, (student_id, slot_id)).fetchone()

                    # Якщо уроків ще взагалі немає, пропускаємо
                    if not last_lesson:
                        continue

                    last_start = datetime.fromisoformat(last_lesson[0])
                    last_end = datetime.fromisoformat(last_lesson[1])

                    lessons_to_add = 4 - active_count

                    for i in range(lessons_to_add):
                        days_shift = 7 * (i + 1)

                        new_start = last_start + timedelta(days=days_shift)
                        new_end = last_end + timedelta(days=days_shift)

                        cursor.execute("""
                            INSERT INTO lessons (
                                slot_id,
                                account_id,
                                start_time,
                                end_time
                            )
                            VALUES (?, ?, ?, ?)
                        """, (
                            slot_id,
                            student_id,
                            new_start.isoformat(sep=' '),
                            new_end.isoformat(sep=' ')
                        ))

                conn.commit()
                print("додалися нові уроки")

            except Exception:
                conn.rollback()
                raise

    def show_lesson_for_student(self, telegram_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            query = cursor.execute("""
            SELECT * from lessons
            WHERE account_id = ?
            AND is_in_past = 0
            ORDER BY start_time ASC
            """, (telegram_id,)).fetchall()

            return query

    def update_lesson(self, lesson_id: int, new_date: str, new_date_end: str, accept = True):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                           UPDATE resheduled_lessons 
                           SET status = ?
                           WHERE lesson_id = ?
                       """, (
                        "accept" if accept else "reject",
                        lesson_id
                    ))
                if accept:
                    # 3. Оновлюємо сам урок
                    cursor.execute("""
                           UPDATE lessons
                           SET start_time = ?,
                               end_time = ?,
                               status = ?
                           WHERE lesson_id = ?
                       """, (
                        new_date,
                        new_date_end,
                        "rescheduled",
                        lesson_id
                    ))

                conn.commit()

            except Exception:
                conn.rollback()
                raise

    def create_rescheduled_request(self,lesson_id: int, new_start: str, reason: str):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            old_lesson = cursor.execute("""
                                   SELECT start_time, end_time
                                   FROM lessons
                                   WHERE lesson_id = ?
                               """, (lesson_id,)).fetchone()[0]


            query = cursor.execute("""
            INSERT INTO resheduled_lessons VALUES(?,?,?,?,?)
            """, (lesson_id,old_lesson, new_start, reason, "waiting"))

        conn.commit()

    def create_cancel_request(self, lesson_id,reason,canceled_by):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            old_lesson = cursor.execute("""
                                   SELECT start_time, end_time
                                   FROM lessons
                                   WHERE lesson_id = ?
                               """, (lesson_id,)).fetchone()

            start_time, end_time = old_lesson

            query = cursor.execute("""
            INSERT INTO cancelled_lessons(
            lesson_id,
            original_start,
            original_end,
            reason,
            status,
            cancelled_by
            ) VALUES(?,?,?,?,?,?)
            """, (lesson_id,start_time,end_time,reason,"unproved",canceled_by))


    def cancel_lesson(self,lesson_id, accepted = True):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            old_lesson = cursor.execute("""
                                               SELECT start_time, end_time
                                               FROM lessons
                                               WHERE lesson_id = ?
                                           """, (lesson_id,)).fetchone()

            start_time, end_time = old_lesson
            try:
                query = cursor.execute("""
                                UPDATE cancelled_lessons
                                SET status = ?,
                                cancelled_at = CURRENT_TIMESTAMP
                                WHERE lesson_id = ?
                                """, ("accepted" if accepted else "rejected", lesson_id,))

                if accepted:
                    query = cursor.execute("""
                    UPDATE lessons
                    SET status = "canceled"
                    WHERE lesson_id = ?
                    """, (lesson_id,))



                conn.commit()

            except Exception:
                conn.rollback()
                raise

    def cancel_slot(self, user_id, slot_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    UPDATE requiring_slots
                    SET status = 'free'
                    WHERE id = ?
                    """,
                    (slot_id,)
                )
                cursor.execute(
                    """
                    DELETE FROM requiring_slots_students
                    WHERE id_of_slot = ?
                      AND student_id = ?
                    """,
                    (slot_id, user_id)
                )

                cursor.execute(
                    """
                    DELETE FROM lessons
                    WHERE slot_id = ?
                      AND account_id = ?
                      AND is_in_past = 0
                    """,
                    (slot_id, user_id)
                )

                conn.commit()
                return True

            except Exception as e:
                conn.rollback()
                print(e)
                return False

    def get_lessons_for_reminder(self, hours_before: int, tolerance_minutes: int = 5) -> list[tuple]:

        KYIV_TZ = ZoneInfo("Europe/Kyiv")

        if hours_before not in (1,4,24):
            raise ValueError("hours_before має бути 1, 4 або 24")

        now = datetime.now(KYIV_TZ)

        target_time = now + timedelta(hours=hours_before)

        window_start = target_time - timedelta(minutes=tolerance_minutes)
        window_end = target_time + timedelta(minutes=tolerance_minutes)

        reminder_columns = {
            1: "reminder_1h_sent",
            4: "reminder_4h_sent",
            24: "reminder_24_sent"

        }

        reminder_column = reminder_columns[hours_before]

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(f"""
            SELECT lesson_id, account_id,start_time, is_paid 
            FROM lessons
            WHERE status IN ('active', 'rescheduled', 'active_onetime_lesson')
            AND is_in_past = 0
            AND {reminder_column} = 0
            AND start_time BETWEEN ? AND ?
            ORDER BY start_time
            """, (window_start.strftime("%Y-%m-%d %H:%M:%S"),
                window_end.strftime("%Y-%m-%d %H:%M:%S")))

            return cursor.fetchall()



    def mark_reminder_as_sent(self, lesson_id: int, time: int):
        columns = {
            24: "reminder_24_sent",
            4: "reminder_4h_sent",
            1: "reminder_1h_sent"
        }

        if time not in columns:
            raise ValueError("time має бути '24h', '4h' або '1h'")

        column = columns[time]

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(f"""
            UPDATE lessons
            SET {column} = 1
            WHERE lesson_id = ?
            """, (lesson_id,))

            return cursor.rowcount > 0


    def request_onetimelesson(self,student_id: int,start_time: str, end_time: str):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                        INSERT INTO lessons (
                            slot_id,
                            account_id,
                            start_time,
                            end_time,
                            is_paid,
                            status
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                None,
                student_id,
                start_time,
                end_time,
                0,
                "pending_one_time_lesson"
            ))

            lesson_id = cursor.lastrowid
            return lesson_id

    def change_status_for_one_time_lesson(self,lesson_id: int, status: str):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
            UPDATE lessons
            SET status = ?
            WHERE lesson_id = ?
            """, (status, lesson_id,))

            return cursor.rowcount > 0


    def get_lessons_by_date(self, today_date: date):
        with sqlite3.connect(self.db_name) as conn:
            date_str = today_date.strftime("%Y-%m-%d")
            cursor = conn.cursor()

            cursor.execute("""
            SELECT
                l.lesson_id,
                l.start_time,
                l.end_time,
                l.is_paid,
                sa.telegr_id,
                s.name
            FROM
                lessons l JOIN students_accounts sa ON l.account_id = sa.telegr_id JOIN students s ON s.student_id = sa.for_student
            WHERE
                DATE(l.start_time) = ?
            AND
                l.status != 'canceled'
            ORDER BY l.start_time
            """,(date_str,))

            return cursor.fetchall()

    def get_lesson(self, lesson_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                        SELECT
                            l.lesson_id,
                            l.start_time,
                            l.end_time,
                            l.status,
                            l.is_paid,
                            s.name,
                            sa.telegr_id
                        FROM lessons l
                        JOIN students_accounts sa
                            ON l.account_id = sa.telegr_id
                        JOIN students s
                            ON s.student_id = sa.for_student
                        WHERE l.lesson_id = ?
                    """, (lesson_id,))

            return cursor.fetchone()


