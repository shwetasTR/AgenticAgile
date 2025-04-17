class FeatureExtractor:
    def __init__(self):
        self.features = []

    def aggregate_features(self, new_features):
        self.features.extend(new_features)

    def process_features(self):
        # Implement feature processing logic here
        processed_features = [feature for feature in self.features if feature is not None]
        return processed_features

    def clear_features(self):
        self.features = []