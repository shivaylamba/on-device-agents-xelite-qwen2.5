from pathlib import Path

import onnx
from onnx import TensorProto, helper


def main():
    out_dir = Path(__file__).resolve().parents[1] / "cache"
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / "toy-add-fp32.onnx"

    x = helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 4])
    y = helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 4])
    z = helper.make_tensor_value_info("z", TensorProto.FLOAT, [1, 4])
    add = helper.make_node("Add", ["x", "y"], ["z"])
    graph = helper.make_graph([add], "toy_add_fp32", [x, y], [z])
    model = helper.make_model(graph, opset_imports=[helper.make_operatorsetid("", 17)])
    model.ir_version = 10
    onnx.save(model, model_path)
    print(model_path)


if __name__ == "__main__":
    main()
