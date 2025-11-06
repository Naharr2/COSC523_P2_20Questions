import json
import random
import pickle
import statistics
from pathlib import Path


class QuestionsGame:
    def __init__(self) -> None:
        self.OBJECTS_DIR = Path.cwd()
        self.ENDPOINT_TO_FILENAME = {
            "living_food_items": "living_food_items.txt",
            "non_animal_food_items": "Non-animal food items.txt",
            "living_fantasy_wildlife": "Living fantasy-wildlife.txt",
            "plants": "Plants.txt",
            "person_role": "Person-role.txt",
            "large_place_geography": "Large place_geography.txt",
            "abstract": "Abstract ideas-objects-events.txt",
            "natural_objects": "Natural Objects.txt",
            "chemicals_nonconsumable": "Chemicals-non-consumable items.txt",
            "common_items": "Common items.txt",
            "uncommon_items": "Uncommon items.txt",
        }

        self.propertiesFile = "property_universe.txt"
        self.properties = self._get_properties()
        self.questionsAsked = 0

        self.lookupFile = "ontology.pickle"
        self.original_lookup_table = self._get_lookup_table()
        self.modified_lookup_table = self.original_lookup_table
        self.possible_nouns: list[str] = []

    # loads context data from premade pickle file
    # generated from OntologyGeneration.ipynb
    def _get_lookup_table(self) -> dict:
        try:
            with open(self.lookupFile, "rb") as f:
                lookup_table = pickle.load(f)
            return lookup_table
        except FileNotFoundError:
            print("Lookup table file not found. Please provide a table.")
            exit(1)

    # load properties from given file
    def _get_properties(self) -> list[str]:
        with open(self.propertiesFile, "r") as f:
            properties = f.read().splitlines()
        return properties

    # error context if no nouns load at beginning of game
    def error_no_nouns(self) -> bool:
        if self.possible_nouns == []:
            print("Error: No nouns available to choose from.")
            return True
        return False

    # error context if no properties load at beginning of game
    def error_no_properties(self) -> bool:
        if self.properties == []:
            print("Error: No properties available to choose from.")
            return True
        return False

    # checks if user wants to exit game, or if response is not yes or no
    # TODO: do we need this, or does _ask_yn cover this?
    def _validate_user_response(self, response: str) -> str:
        response = response.lower()
        if response == "exit":
            print("Exiting the game. Goodbye!")
            exit(0)
        while response not in ["yes", "no"]:
            response = input("Please respond with 'yes' or 'no': ").lower()
        return response

    # updates question count, asks question, gets user response
    def _ask_yn(self, prompt: str) -> bool:
        self.questionsAsked += 1
        while True:
            ans = (
                input(f"Question {self.questionsAsked}: {prompt} (yes/no): ")
                .strip()
                .lower()
            )
            if ans in ("y", "yes"):
                return True
            if ans in ("n", "no"):
                return False
            print("Invalid response. Please answer 'yes' or 'no'.")

    # loads narrowed down list of objects/nouns based on initial questions
    def _load_objects(self, filename: str) -> list[str]:
        path = self.OBJECTS_DIR / filename
        print(path)
        if not path.exists():
            print(f"Error: Required noun file not found: {path}")
            return []
        with path.open("r", encoding="utf-8-sig") as f:
            items = [line.strip() for line in f if line.strip()]
        return items

    # decision tree for narrowing down nouns for first few questions
    def _run_initial_questions(self) -> tuple[str, list[str]]:
        # Q1
        alive = self._ask_yn("Has it, or has it ever, been alive?")
        if alive:
            # Q2
            person = self._ask_yn("Is it a person?")
            if person:
                endpoint = "person_role"
            else:
                # Q3
                animal = self._ask_yn("Is it an animal?")
                if animal:
                    # Q4
                    edible = self._ask_yn("Do people usually eat it?")
                    endpoint = (
                        "living_food_items"
                        if edible
                        else "living_fantasy_wildlife"
                    )
                else:
                    endpoint = "plants"
        else:
            # Q5
            place = self._ask_yn("Is it a place?")
            if place:
                endpoint = "large_place_geography"
            else:
                # Q6
                physical = self._ask_yn("Is it a physical object?")
                if not physical:
                    endpoint = "abstract"
                else:
                    # Q7
                    man_made = self._ask_yn("Is it man-made?")
                    if not man_made:
                        endpoint = "natural_objects"
                    else:
                        # Q8
                        mechanical = self._ask_yn("Is it mechanical?")
                        if mechanical:
                            # Q9
                            used_daily = self._ask_yn("Is it used daily?")
                            endpoint = (
                                "common_items"
                                if used_daily
                                else "uncommon_items"
                            )
                        else:
                            # Q10
                            can_eat = self._ask_yn("Can you eat it?")
                            endpoint = (
                                "non_animal_food_items"
                                if can_eat
                                else "chemicals_nonconsumable"
                            )
        filename = self.ENDPOINT_TO_FILENAME[endpoint]
        objects = self._load_objects(filename)
        print(
            f"\n➡ Category: {endpoint}  |  File: {filename}  |  Loaded {len(objects)} objects."
        )
        return endpoint, objects

    # finds category that best splits the current possible nouns
    def _calculate_category_scores(self) -> tuple:
        best_category = None
        max_score = -1
        print(self.possible_nouns)
        candidate_nouns = {
            noun: self.original_lookup_table[noun]
            for noun in self.possible_nouns
        }
        all_categories = set()
        for noun in self.possible_nouns:
            print(noun)
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
    def _calculate_property_scores(self) -> tuple:
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

    # finds metadata value that best splits the current possible nouns
    def _score_metadata_questions(self) -> tuple:
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

    # determine best type of guess for next question
    def _find_best_guess(self) -> tuple:
        category = self._calculate_category_scores()
        property = self._calculate_property_scores()
        metadata = self._score_metadata_questions()

        return max([category, property, metadata])

    # create the question string based on best guess data
    def _form_question(self, best_guess_data: tuple) -> str:
        score, q_type, q_data = best_guess_data

        if score <= 0:
            print(score, q_type, q_data)
            return "Bad score"  # no valid questions can be formed
        if q_type == "category":
            return f"Does it involve {q_data}?"
        elif q_type == "property":
            return f"Does it have the property of {q_data}?"
        elif q_type == "metadata":
            if not q_data:
                return "I'm not sure what to ask next."
            prop_name, threshold = q_data
            return f"Is its '{prop_name}' value considered high (e.g., more than {threshold:.2f})?"
        return "I'm not sure what to ask next."

    # TODO: maybe this needs to be renamed to _form_final_guess?
    def _form_guess(self) -> str:
        if len(self.possible_nouns) == 1:
            return f"Are you thinking of {self.possible_nouns[0]}?"
        elif self.possible_nouns:  # More than 1 left, pick one
            guess_noun = random.choice(self.possible_nouns)
            return f"Are you thinking of {guess_noun}?"
        else:  # No nouns left
            return "I've run out of options and have no guess! You win."

    # updates possible nouns based on user response
    def _update_possible_nouns(
        self, question_data: tuple, response: str
    ) -> None:
        q_type, q_info = question_data[1], question_data[2]
        new_possible_nouns = []

        if (
            self.questionsAsked <= 10
            and q_type == "category"
            and question_data[0] == 0
        ):
            pass

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

    # actual gameplay
    def startGame(self) -> None:
        if self.error_no_properties():
            exit(1)
        self.possible_nouns = []
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

        endpoint, self.possible_nouns = self._run_initial_questions()
        # uncomment below to check the pickle file
        # TODO: remove before submission
        # with open("output.json", "w") as f:
        #     json.dump(self.original_lookup_table, f, cls=SetEncoder, indent=2)

        if self.error_no_nouns():
            exit(1)

        print(f"({len(self.possible_nouns)} possibilities remaining...)\n")

        best_question_data = None
        while self.questionsAsked <= 20:
            guess = ""

            if len(self.possible_nouns) == 1:
                break  # Exit loop to make final guess
            elif not self.possible_nouns:
                print(
                    "I've run out of options, something must have gone wrong!"
                )
                return
            else:
                # Find the best question to ask
                best_question_data = self._find_best_guess()
                guess = self._form_question(best_question_data)

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

        # final guess
        final_guess = self._form_guess()
        print(final_guess)

        if final_guess.startswith("I've run out"):
            return  # Game already ended

        user_response = input("Your response (yes/no): ")
        validated_response = self._validate_user_response(user_response)
        if validated_response == "yes":
            print("I win! Thanks for playing.")
        else:
            print("You win.")


# helper class for making sets printable in JSON
# TODO: remove before submission
class SetEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, set):
            return list(o)  # Convert set to list
        return json.JSONEncoder.default(self, o)


if __name__ == "__main__":
    game = QuestionsGame()
    game.startGame()
