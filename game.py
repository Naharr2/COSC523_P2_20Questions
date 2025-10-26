import random
import pickle


class QuestionsGame:
    def __init__(self) -> None:
        self.nounFile = "noun_universe.txt"
        self.nouns = self._get_nouns()
        self.propertiesFile = "property_universe.txt"
        self.properties = self._get_properties()
        self.questionsAsked = 0
        # we can change these later, just using them for now
        self.general_categories = [
            "peron",
            "place",
            "thing",
            "animal",
            "plant",
            "action",
        ]
        self.lookupFile = "ontology.pickle"
        self.original_lookup_table = self._get_lookup_table()
        self.modified_lookup_table = self.original_lookup_table
        self.possible_nouns = self.nouns

    def _get_lookup_table(self) -> dict:
        try:
            with open(self.lookupFile, "rb") as f:
                lookup_table = pickle.load(f)
            return lookup_table
        except FileNotFoundError:
            print("Lookup table file not found. Please provide a table.")
            exit(1)

    def _get_nouns(self) -> list[str]:
        with open(self.nounFile, "r") as f:
            nouns = f.read().splitlines()
        return nouns

    def _get_properties(self) -> list[str]:
        with open(self.propertiesFile, "r") as f:
            properties = f.read().splitlines()
        return properties

    def error_no_nouns(self) -> bool:
        if self.nouns == []:
            print("Error: No nouns available to choose from.")
            return True
        return False

    def error_no_properties(self) -> bool:
        if self.properties == []:
            print("Error: No properties available to choose from.")
            return True
        return False

    def _validate_user_response(self, response: str) -> str:
        response = response.lower()
        if response == "exit":
            print("Exiting the game. Goodbye!")
            exit(0)
        while response not in ["yes", "no"]:
            response = input("Please respond with 'yes' or 'no': ").lower()
        return response

    def _find_best_guess(self):
        best_question = None
        max_score = -1

        # guess by category
        # get all categories in our current guess pool
        categories = []
        for noun in self.modified_lookup_table:
            noun_categories = self.modified_lookup_table[noun]["categories"]
            for category in noun_categories:
                if category not in categories:
                    categories.append(category)
        # find out how many nouns in our current guess pool have the category we're thinking of
        for category in categories:  # look at each category
            yes_count = 0
            # look at each noun in our current guess pool
            for noun in self.possible_nouns:
                if category in self.modified_lookup_table[noun]["categories"]:
                    yes_count += 1
            # create the score for this category
            category_score = yes_count * (len(self.possible_nouns) - yes_count)
            if category_score > max_score:
                max_score = category_score
                best_question = f"Is it a {category}?"
                yes_count = None
        return best_question

    def _form_guess(self) -> str:
        if self.questionsAsked == 0:
            # beginning of the game, pick one of the general categories
            category = random.choice(self.general_categories)
            return f"Is it a {category}?"
        elif self.questionsAsked < 20:
            #  middle of the game, this will be based on our prev guesses and responses
            return "Thinking!"  # placeholder for now
        else:
            # end of game, must make a guess
            # expected logic: if remaining nouns is 1, guess that noun
            # else, pick a random noun from remaining nouns
            return "Are you thinking of [noun]?"  # replace with noun

    def startGame(self) -> None:
        if self.error_no_nouns() or self.error_no_properties():
            exit(1)
        self.guessable_nouns = self.nouns
        self.questionsAsked = 0

        print("Welcome to Team 23's 20 Questions Game!\n")
        print(
            "Please pick a noun from the noun universe, and I will try to guess it!\n"
        )
        print(
            "I will ask you yes or no questions, please only respond with 'yes' or 'no'.\n"
        )
        print("You can type 'exit' at any time to quit the game.\n")
        print("Ready? Let's begin!\n")

        while self.questionsAsked <= 20:
            guess = self._form_guess()
            print(guess)
            user_response = input("Your response (yes/no): ")
            validated_response = self._validate_user_response(user_response)
            self.questionsAsked += 1


if __name__ == "__main__":
    game = QuestionsGame()
    game.startGame()
