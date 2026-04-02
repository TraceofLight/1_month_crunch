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


if __name__ == "__main__":
    QuizGame()
