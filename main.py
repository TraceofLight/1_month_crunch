import json
import sys
from pathlib import Path


STATE_PATH = Path(__file__).with_name("state.json")


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
        print("\n----------------------------------------")
        print(f"[문제 {number}]")
        print(self.question)
        print()
        for index, choice in enumerate(self.choices, start=1):
            print(f"{index}. {choice}")
        print()

    def is_correct(self, selected_answer):
        return selected_answer == self.answer

    def to_dict(self):
        return {
            "question": self.question,
            "choices": self.choices,
            "answer": self.answer,
        }

    @classmethod
    def from_dict(cls, data):
        question = data["question"]
        choices = data["choices"]
        answer = data["answer"]

        if not isinstance(question, str) or not question.strip():
            raise ValueError("question")
        if not isinstance(choices, list) or len(choices) != 4:
            raise ValueError("choices")
        if any(not isinstance(choice, str) or not choice.strip() for choice in choices):
            raise ValueError("choices")
        if not isinstance(answer, int) or not 1 <= answer <= 4:
            raise ValueError("answer")

        return cls(question.strip(), [choice.strip() for choice in choices], answer)


class QuizGame:
    def __init__(self):
        self.state_path = STATE_PATH
        self.quizzes = []
        self.best_score = None
        self.is_running = True
        self.load_state()

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
                self.handle_safe_exit()

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
        if not self.quizzes:
            print("\n등록된 퀴즈가 없습니다.")
            return

        print(f"\n퀴즈를 시작합니다! (총 {len(self.quizzes)}문제)")
        correct_answers = 0

        for number, quiz in enumerate(self.quizzes, start=1):
            quiz.display(number)
            selected_answer = self.ask_number("정답 입력 (1-4): ", 1, 4)
            if quiz.is_correct(selected_answer):
                correct_answers += 1
                print("정답입니다!")
            else:
                print(f"오답입니다. 정답은 {quiz.answer}번입니다.")

        total_questions = len(self.quizzes)
        score = int(correct_answers / total_questions * 100)
        print("\n========================================")
        print(f"결과: {total_questions}문제 중 {correct_answers}문제 정답! ({score}점)")
        if self.update_best_score(correct_answers, total_questions, score):
            print("새로운 최고 점수입니다!")
        else:
            print("현재 최고 점수는 유지됩니다.")
        print("========================================")
        self.save_state()

    def add_quiz(self):
        print("\n새로운 퀴즈를 추가합니다.")
        question = self.ask_text("문제를 입력하세요: ")
        choices = [self.ask_text(f"선택지 {number}: ") for number in range(1, 5)]
        answer = self.ask_number("정답 번호 (1-4): ", 1, 4)

        self.quizzes.append(Quiz(question, choices, answer))
        self.save_state()
        print("퀴즈가 추가되었습니다!")

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

    def exit_game(self):
        self.save_state()
        print("\n데이터를 저장하고 종료합니다.")
        self.is_running = False

    def handle_safe_exit(self):
        print("\n입력이 중단되어 데이터를 저장한 뒤 안전하게 종료합니다.")
        self.save_state()
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

    def load_state(self):
        if not self.state_path.exists():
            self.quizzes = self.build_default_quizzes()
            self.best_score = None
            print(f"{self.state_path.name} 파일이 없어 기본 퀴즈로 시작합니다.")
            return

        try:
            with self.state_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            self.quizzes = [Quiz.from_dict(item) for item in data.get("quizzes", [])]
            self.best_score = self.normalize_best_score(data.get("best_score"))
            print(self.build_load_message())
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            print(f"{self.state_path.name} 파일이 없거나 손상되어 기본 퀴즈 데이터로 복구합니다.")
            self.quizzes = self.build_default_quizzes()
            self.best_score = None
            self.save_state()

    def normalize_best_score(self, best_score):
        if best_score is None:
            return None
        if not isinstance(best_score, dict):
            raise ValueError("best_score")

        correct = best_score["correct"]
        total = best_score["total"]
        score = best_score["score"]

        if not all(isinstance(value, int) for value in [correct, total, score]):
            raise ValueError("best_score")
        if correct < 0 or total < 0 or score < 0:
            raise ValueError("best_score")

        return {
            "correct": correct,
            "total": total,
            "score": score,
        }

    def build_load_message(self):
        if self.best_score is None:
            best_score_text = "없음"
        else:
            best_score_text = f"{self.best_score['score']}점"
        return f"저장된 데이터를 불러왔습니다. (퀴즈 {len(self.quizzes)}개, 최고점수 {best_score_text})"

    def save_state(self):
        data = {
            "quizzes": [quiz.to_dict() for quiz in self.quizzes],
            "best_score": self.best_score,
        }

        try:
            with self.state_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except OSError:
            print(f"{self.state_path.name} 파일을 저장하지 못했습니다.")


if __name__ == "__main__":
    QuizGame().run()
