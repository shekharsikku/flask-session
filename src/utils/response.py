from flask import make_response, jsonify


class ApiResponse:
    def __init__(self, code: int, message: str, data: any = None, error: any = None):
        self.code = code
        self.message = message
        self.data = data
        self.error = error

    def api_response(self):
        success = True if self.code < 400 else False
        response = {"message": self.message, "success": success}

        if self.data is not None:
            response["data"] = self.data

        if self.error is not None:
            response["error"] = self.error

        return response

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.__init__(*args, **kwargs)
        return make_response(jsonify(instance.api_response()), instance.code)
