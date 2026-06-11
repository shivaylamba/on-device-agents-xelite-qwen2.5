import argparse
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort


def register_qnn():
    import onnxruntime_qnn as qnn

    ort.register_execution_provider_library("QNNExecutionProvider", qnn.get_library_path())
    return qnn


def provider_options(qnn, backend: str):
    if backend == "htp":
        return {"backend_path": qnn.get_qnn_htp_path()}
    if backend == "cpu":
        return {"backend_path": qnn.get_qnn_cpu_path()}
    raise ValueError(f"Unsupported backend: {backend}")


def shape_for_input(input_meta):
    shape = []
    for index, dim in enumerate(input_meta.shape):
        if isinstance(dim, int) and dim > 0:
            shape.append(dim)
        elif index == 0:
            shape.append(1)
        else:
            shape.append(1)
    return shape


def dtype_for_input(input_meta):
    type_map = {
        "tensor(float)": np.float32,
        "tensor(float16)": np.float16,
        "tensor(double)": np.float64,
        "tensor(int64)": np.int64,
        "tensor(int32)": np.int32,
        "tensor(int8)": np.int8,
        "tensor(uint8)": np.uint8,
    }
    return type_map.get(input_meta.type, np.float32)


def load_inputs(session, inputs_path: Path | None):
    if inputs_path:
        payload = json.loads(inputs_path.read_text(encoding="utf-8"))
        return {
            name: np.asarray(value)
            for name, value in payload.items()
        }

    generated = {}
    for input_meta in session.get_inputs():
        dtype = dtype_for_input(input_meta)
        generated[input_meta.name] = np.ones(shape_for_input(input_meta), dtype=dtype)
    return generated


def summarize_outputs(outputs):
    summary = []
    for index, output in enumerate(outputs):
        array = np.asarray(output)
        summary.append(
            {
                "index": index,
                "shape": list(array.shape),
                "dtype": str(array.dtype),
                "min": float(array.min()) if array.size else None,
                "max": float(array.max()) if array.size else None,
                "mean": float(array.mean()) if array.size else None,
            }
        )
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run an ONNX model through ONNX Runtime QNN EP.")
    parser.add_argument("--model", required=True, help="Path to a QNN-compatible ONNX model.")
    parser.add_argument("--backend", choices=["htp", "cpu"], default="htp")
    parser.add_argument("--inputs", help="Optional JSON file mapping input names to arrays.")
    parser.add_argument("--no-cpu-fallback", action="store_true", help="Fail if QNN EP does not own the session.")
    args = parser.parse_args()

    qnn = register_qnn()
    providers = [
        ("QNNExecutionProvider", provider_options(qnn, args.backend)),
        "CPUExecutionProvider",
    ]
    session = ort.InferenceSession(args.model, providers=providers)
    active_providers = session.get_providers()

    if args.no_cpu_fallback and "QNNExecutionProvider" not in active_providers:
        raise RuntimeError(f"QNNExecutionProvider did not own the session. Active providers: {active_providers}")

    inputs = load_inputs(session, Path(args.inputs) if args.inputs else None)
    outputs = session.run(None, inputs)
    print(
        json.dumps(
            {
                "model": str(Path(args.model).resolve()),
                "backend": args.backend,
                "requested_providers": [provider[0] if isinstance(provider, tuple) else provider for provider in providers],
                "active_providers": active_providers,
                "qnn_ep_active": "QNNExecutionProvider" in active_providers,
                "inputs": {
                    name: {"shape": list(value.shape), "dtype": str(value.dtype)}
                    for name, value in inputs.items()
                },
                "outputs": summarize_outputs(outputs),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
