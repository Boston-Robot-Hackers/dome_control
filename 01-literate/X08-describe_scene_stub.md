---
version: "1.0"
generated: "2026-05-04"
---

# Describe Scene Stub Node (Appendix)

`describe_scene_stub_node.py` is a temporary placeholder for the real `/describe_scene` service.

```python
class DescribeSceneStubNode(Node):
    def __init__(self):
        super().__init__("describe_scene_stub")
        self.service = self.create_service(Trigger, "/describe_scene", self.describe_scene)

    def describe_scene(self, request, response):
        response.success = True
        response.message = "I see 2 cups and 1 can"
        return response
```

Returns a hardcoded string. Purpose: allows the behavior manager pipeline (`BehaviorManagerNode` → `/describe_scene` → `/announcement` → `SpeechOutputNode`) to be smoke-tested without the actual object detection stack running.

This node should be replaced with a real `/describe_scene` service backed by `/targets/confirmed` from the oak_roboflow detection pipeline. See `current.md` next steps.
