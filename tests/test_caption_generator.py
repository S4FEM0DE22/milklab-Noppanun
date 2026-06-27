import caption_generator


def test_build_menu_context_includes_price_and_ingredients():
    menu_payload = {
        "menu": {
            "name": "นมหมีฮอกไกโด",
            "price": 65,
            "ingredients": ["นมสดฮอกไกโด", "วิปครีม"],
        }
    }

    context = caption_generator._build_menu_context(menu_payload)

    assert "ชื่อเมนู: นมหมีฮอกไกโด" in context
    assert "ราคา: 65 บาท" in context
    assert "ส่วนผสม: นมสดฮอกไกโด, วิปครีม" in context


def test_generate_caption_retries_when_output_is_too_long(monkeypatch):
    responses = ["x" * 300, "แคปชั่นสั้นที่ผ่านเกณฑ์"]

    class FakeModels:
        def __init__(self, responses):
            self._responses = list(responses)
            self.calls = 0

        def generate_content(self, **kwargs):
            self.calls += 1
            text = self._responses.pop(0)
            return type("Response", (), {"text": text})()

    class FakeClient:
        def __init__(self, api_key=None, responses=None):
            self.models = FakeModels(responses or [])

    monkeypatch.setattr(caption_generator.genai, "Client", lambda api_key=None: FakeClient(
        api_key=api_key, responses=responses))

    caption = caption_generator.generate_caption(
        "นมหมีฮอกไกโด", api_key="fake-key")

    assert caption == "แคปชั่นสั้นที่ผ่านเกณฑ์"


def test_generate_captions_supports_style_variants(monkeypatch):
    responses = ["cute", "minimal", "gen-z"]

    class FakeModels:
        def __init__(self, responses):
            self._responses = responses
            self.calls = 0

        def generate_content(self, **kwargs):
            self.calls += 1
            text = self._responses.pop(0)
            return type("Response", (), {"text": text})()

    class FakeClient:
        def __init__(self, api_key=None, responses=None):
            self.models = FakeModels(responses or [])

    monkeypatch.setattr(caption_generator.genai, "Client", lambda api_key=None: FakeClient(
        api_key=api_key, responses=responses))

    captions = caption_generator.generate_captions(
        "นมหมีฮอกไกโด",
        styles=["cute", "minimal", "gen-z"],
        api_key="fake-key",
    )

    assert captions == ["cute", "minimal", "gen-z"]
