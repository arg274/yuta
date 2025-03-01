import pickle


class ModelManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._model = None
            self._label_encoder = None
            self._initialized = True

    def load_models(self):
        if self._model is None or self._label_encoder is None:
            try:
                with open("ml/weights/xgboost_model.pkl", "rb") as f:
                    self._model = pickle.load(f)
                with open("ml/weights/label_encoder.pkl", "rb") as f:
                    self._label_encoder = pickle.load(f)
            except Exception as e:
                raise RuntimeError(f"Failed to load models: {str(e)}")

        return self._model, self._label_encoder

    @property
    def model(self):
        if self._model is None:
            self.load_models()
        return self._model

    @property
    def label_encoder(self):
        if self._label_encoder is None:
            self.load_models()
        return self._label_encoder
