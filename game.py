import random
import pickle
import statistics
from pathlib import Path


class QuestionsGame:
    def __init__(self) -> None:
        # self.OBJECTS_DIR = Path.home()
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

    # finds category that best splits the current possible nouns
    def _calculate_category_scores(self):
        best_category = None
        max_score = -1

        candidate_nouns = {
            noun: self.original_lookup_table[noun]
            for noun in self.possible_nouns
        }
        all_categories = set()
        for noun in self.possible_nouns:
            noun_data = self.original_lookup_table.get(noun, {})
            all_categories.update(noun_data.get("categories", []))

        if not all_categories:
            return (-1, "category", None)

        total_candidaates = len(self.possible_nouns)
        for category in all_categories:
            yes_count = 0
            for noun, noun_data in candidate_nouns.items():
                if category in noun_data.get("categories", []):
                    yes_count += 1
            no_count = total_candidaates - yes_count
            score = yes_count * no_count
            if score > max_score:
                max_score = score
                best_category = category

        return (max_score, "category", best_category)

    # finds property that best splits the current possible nouns
    def _calculate_property_scores(self):
        best_property = None
        max_score = -1

        candidate_nouns = {
            noun: self.original_lookup_table[noun]
            for noun in self.possible_nouns
        }
        all_properties = set()
        for noun in self.possible_nouns:
            noun_data = self.original_lookup_table.get(noun, {})
            all_properties.update(noun_data.get("properties", []))

        if not all_properties:
            return (-1, "property", None)

        total_candidates = len(self.possible_nouns)
        for prop in all_properties:
            yes_count = 0
            for noun, noun_data in candidate_nouns.items():
                if prop in noun_data.get("properties", []):
                    yes_count += 1
            no_count = total_candidates - yes_count
            score = yes_count * no_count
            if score > max_score:
                max_score = score
                best_property = prop

        return (max_score, "property", best_property)

    def _score_metadata_questions(self):
        best_meta_prop = None
        best_threshold = None
        max_score = -1
        metadata = None

        candidate_nouns = {
            noun: self.original_lookup_table[noun]
            for noun in self.possible_nouns
        }
        all_meta_properties = set()
        for noun in self.possible_nouns:
            noun_data = self.original_lookup_table.get(noun, {})
            all_meta_properties.update(noun_data.get("metadata", {}).keys())

        if not all_meta_properties:
            return (max_score, "metadata", metadata)

        total_candidates = len(self.possible_nouns)
        for meta_prop in all_meta_properties:
            # get mean value for the property from all possible nouns
            mean_list = []
            for noun, noun_data in candidate_nouns.items():
                if meta_prop in noun_data.get("metadata", {}):
                    mean_list.append(
                        noun_data["metadata"][meta_prop].get("mean", 0)
                    )

            if not mean_list:
                continue  # property isn't in any possible nouns

            threshold = statistics.mean(mean_list)
            yes_count = 0
            for noun, noun_data in candidate_nouns.items():
                if meta_prop in noun_data.get("metadata", {}):
                    if (
                        noun_data["metadata"][meta_prop].get("mean", 0)
                        >= threshold
                    ):
                        yes_count += 1  # noun meets the threshold
            no_count = total_candidates - yes_count
            score = yes_count * no_count
            if score > max_score:
                max_score = score
                best_meta_prop = meta_prop
                best_threshold = threshold
                metadata = (best_meta_prop, best_threshold)

        return (max_score, "metadata", metadata)

    def _find_best_guess(self):
        category = self._calculate_category_scores()
        property = self._calculate_property_scores()
        metadata = self._score_metadata_questions()

        return max([category, property, metadata])

    def _form_question(self):
        score, q_type, q_data = self._find_best_guess()

        if score <= 0:
            return "Bad score"  # no valid questions can be formed
        if q_type == "category":
            return f"Does it involve {q_data}?"
        elif q_type == "property":
            return f"Does it have the property of {q_data}?"
        elif q_type == "metadata":
            # q_data may be None when no metadata question is available; guard against that
            if not q_data:
                return "I'm not sure what to ask next."
            prop_name, threshold = q_data
            return f"Is its '{prop_name}' value considered high (e.g., more than {threshold:.2f})?"
        return "I'm not sure what to ask next."

    def _form_guess(self) -> str:
        if self.questionsAsked == 0:
            # beginning of the game, pick one of the general categories
            category = random.choice(self.general_categories)
            return f"Is it a {category}?"
        elif self.questionsAsked < 20:
            #  middle of the game, this will be based on our prev guesses and responses
            return self._form_question()
        else:
            # end of game, must make a guess
            # expected logic: if remaining nouns is 1, guess that noun
            # else, pick a random noun from remaining nouns
            if len(self.possible_nouns) == 1:
                return f"Are you thinking of {self.possible_nouns[0]}?"
            elif self.possible_nouns:  # More than 1 left, pick one
                guess_noun = random.choice(self.possible_nouns)
                return f"Are you thinking of {guess_noun}?"
            else:  # No nouns left
                return "I've run out of options and have no guess! You win."

    def _update_possible_nouns(
        self, question_data: tuple, response: str
    ) -> None:
        q_type, q_info = question_data[1], question_data[2]
        new_possible_nouns = []

        if response == "yes":
            for noun in self.possible_nouns:
                noun_data = self.original_lookup_table.get(noun, {})

                if q_type == "category":
                    if q_info in noun_data.get("categories", []):
                        new_possible_nouns.append(noun)

                elif q_type == "property":
                    if q_info in noun_data.get("properties", []):
                        new_possible_nouns.append(noun)

                elif q_type == "metadata":
                    prop_name, threshold = q_info
                    metadata = noun_data.get("metadata", {}).get(prop_name, {})
                    mean_val = metadata.get("mean")
                    if mean_val is not None and mean_val > threshold:
                        new_possible_nouns.append(noun)

        elif response == "no":
            for noun in self.possible_nouns:
                noun_data = self.original_lookup_table.get(noun, {})

                if q_type == "category":
                    if q_info not in noun_data.get("categories", []):
                        new_possible_nouns.append(noun)

                elif q_type == "property":
                    if q_info not in noun_data.get("properties", []):
                        new_possible_nouns.append(noun)

                elif q_type == "metadata":
                    prop_name, threshold = q_info
                    metadata = noun_data.get("metadata", {}).get(prop_name, {})
                    mean_val = metadata.get("mean")
                    if mean_val is None or mean_val <= threshold:
                        new_possible_nouns.append(noun)

        self.possible_nouns = new_possible_nouns

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

        best_question_data = None
        while self.questionsAsked <= 20:
            guess = ""
            if self.questionsAsked == 0:
                # Handle the first question (general category)
                category = random.choice(self.general_categories)
                guess = f"Is it a {category}?"
                # This is a simple heuristic, so we'll just update based on it
                best_question_data = (0, "category", category)

            # Check for win condition (only 1 noun left)
            elif len(self.possible_nouns) == 1:
                print(f"I've got it! Only one possibility left.")
                break  # Exit loop to make final guess

            # Check for lose condition (no nouns left)
            elif not self.possible_nouns:
                print("I've run out of options! You win.")
                return  # Exit game

            else:
                # Find the best question to ask
                best_question_data = self._find_best_guess()
                # FIX: Pass the data to _form_question
                guess = self._form_question()

                if guess == "I am stuck and cannot form a new question.":
                    print(guess)
                    break  # Exit loop to make final guess

            print(f"Question {self.questionsAsked + 1}: {guess}")

            user_response = input("Your response (yes/no): ")
            validated_response = self._validate_user_response(user_response)

            # Update the list!
            if best_question_data:
                self._update_possible_nouns(
                    best_question_data, validated_response
                )

            self.questionsAsked += 1
            print(f"({len(self.possible_nouns)} possibilities remaining...)\n")

        # --- End of Loop: Make Final Guess ---
        print("\nOkay, I've asked 20 questions. Time for my final guess!")
        final_guess = self._form_guess()
        print(final_guess)

        if final_guess.startswith("I've run out"):
            return  # Game already ended

        user_response = input("Your response (yes/no): ")
        validated_response = self._validate_user_response(user_response)
        if validated_response == "yes":
            print("I win! Thanks for playing.")
        else:
            print("Darn! You win.")


if __name__ == "__main__":
    game = QuestionsGame()
    game.startGame()
