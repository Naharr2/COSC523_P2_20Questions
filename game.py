class QuestionsGame:
    def __init__(self) -> None:
        self.nounFile = "noun_universe.txt"
        self.nouns = self._get_nouns()
        self.propertiesFile = "property_universe.txt"
        self.properties = self._get_properties()

    def _get_nouns(self) -> list[str]:
        with open(self.nounFile, "r") as f:
            nouns = f.read().splitlines()
        return nouns

    def _get_properties(self) -> list[str]:
        with open(self.propertiesFile, "r") as f:
            properties = f.read().splitlines()
        return properties


if __name__ == "__main__":
    game = QuestionsGame()
    print("Nouns:", game.nouns)
    print("Properties:", game.properties)
