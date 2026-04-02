import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


class SafeExit(Exception):
    pass


class Quiz:
    def __init__(self, question, choices, answer):
        self.question = question
        self.choices = choices
        self.answer = answer

    def display(self, number):
        print(f"[문제 {number}]")
        print(self.question)
        for index, choice in enumerate(self.choices, start=1):
            print(f"{index}. {choice}")

    def is_correct(self, selected_answer):
        return selected_answer == self.answer


class QuizGame:
    def __init__(self):
        self.quizzes = self.build_default_quizzes()
        self.best_score = None
        self.is_running = True

    def build_default_quizzes(self):
        return [
            Quiz(
                "Python의 창시자는 누구인가요?",
                ["Guido van Rossum", "Linus Torvalds", "James Gosling", "Bjarne Stroustrup"],
                1,
            ),
            Quiz(
                "키와 값을 함께 저장하는 Python 자료형은 무엇인가요?",
                ["list", "tuple", "set", "dict"],
                4,
            ),
            Quiz(
                "함수를 정의할 때 사용하는 키워드는 무엇인가요?",
                ["func", "def", "lambda", "return"],
                2,
            ),
            Quiz(
                "len([1, 2, 3, 4])의 결과는 무엇인가요?",
                ["2", "3", "4", "5"],
                3,
            ),
            Quiz(
                "예외 처리를 시작할 때 가장 먼저 쓰는 키워드는 무엇인가요?",
                ["catch", "except", "try", "finally"],
                3,
            ),
            Quiz(
                "조건이 거짓일 때 다른 분기를 실행하는 키워드는 무엇인가요?",
                ["elif", "else", "for", "while"],
                2,
            ),
        ]

    def run(self):
        while self.is_running:
            try:
                self.show_menu()
                selected_menu = self.ask_number("선택: ", 1, 5)
                self.handle_menu(selected_menu)
            except SafeExit:
                print("\n입력이 중단되어 종료합니다.")
                self.is_running = False

    def show_menu(self):
        print("\n========================================")
        print("        나만의 퀴즈 게임")
        print("========================================")
        print("1. 퀴즈 풀기")
        print("2. 퀴즈 추가")
        print("3. 퀴즈 목록")
        print("4. 점수 확인")
        print("5. 종료")
        print("========================================")

    def handle_menu(self, selected_menu):
        if selected_menu == 1:
            self.play_quiz()
        elif selected_menu == 2:
            self.add_quiz()
        elif selected_menu == 3:
            self.show_quiz_list()
        elif selected_menu == 4:
            self.show_best_score()
        else:
            self.exit_game()

    def play_quiz(self):
        print("\n퀴즈 풀기 기능은 준비 중입니다.")

    def add_quiz(self):
        print("\n퀴즈 추가 기능은 준비 중입니다.")

    def show_quiz_list(self):
        if not self.quizzes:
            print("\n등록된 퀴즈가 없습니다.")
            return

        print(f"\n등록된 퀴즈 목록 (총 {len(self.quizzes)}개)")
        print("----------------------------------------")
        for index, quiz in enumerate(self.quizzes, start=1):
            print(f"[{index}] {quiz.question}")
        print("----------------------------------------")

    def show_best_score(self):
        if self.best_score is None:
            print("\n아직 퀴즈를 풀지 않아 최고 점수가 없습니다.")
            return

        print(
            f"\n최고 점수: {self.best_score['score']}점 "
            f"({self.best_score['total']}문제 중 {self.best_score['correct']}문제 정답)"
        )

    def update_best_score(self, correct_answers, total_questions, score):
        current_best = self.best_score
        if current_best is None or score > current_best["score"]:
            self.best_score = {
                "correct": correct_answers,
                "total": total_questions,
                "score": score,
            }
            return True
        return False

    def exit_game(self):
        print("\n프로그램을 종료합니다.")
        self.is_running = False

    def ask_text(self, prompt):
        while True:
            value = self.read_input(prompt).strip()
            if value:
                return value
            print("빈 입력입니다. 내용을 다시 입력하세요.")

    def ask_number(self, prompt, min_value, max_value):
        while True:
            raw_value = self.read_input(prompt).strip()
            if not raw_value:
                print(f"빈 입력입니다. {min_value}-{max_value} 사이의 숫자를 입력하세요.")
                continue

            try:
                value = int(raw_value)
            except ValueError:
                print(f"잘못된 입력입니다. {min_value}-{max_value} 사이의 숫자를 입력하세요.")
                continue

            if not min_value <= value <= max_value:
                print(f"잘못된 입력입니다. {min_value}-{max_value} 사이의 숫자를 입력하세요.")
                continue

            return value

    def read_input(self, prompt):
        try:
            return input(prompt)
        except (KeyboardInterrupt, EOFError):
            raise SafeExit


if __name__ == "__main__":
    QuizGame().run()
