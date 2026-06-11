import json
import sys

import onnxruntime as ort


def main() -> int:
    result = {
        "python": sys.executable,
        "onnxruntime_version": getattr(ort, "__version__", "unknown"),
        "providers_before_registration": ort.get_available_providers(),
        "qnn_module": None,
        "qnn_ep_registered": False,
        "providers_after_registration": None,
        "ep_devices": [],
    }

    try:
        import onnxruntime_qnn as qnn

        result["qnn_module"] = {
            "library_path": qnn.get_library_path(),
            "qnn_htp_path": qnn.get_qnn_htp_path(),
            "qnn_cpu_path": qnn.get_qnn_cpu_path(),
        }
        ort.register_execution_provider_library("QNNExecutionProvider", qnn.get_library_path())
        result["qnn_ep_registered"] = "QNNExecutionProvider" in ort.get_available_providers()
        result["providers_after_registration"] = ort.get_available_providers()
        if hasattr(ort, "get_ep_devices"):
            result["ep_devices"] = [repr(device) for device in ort.get_ep_devices()]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    print(json.dumps(result, indent=2))
    return 0 if result["qnn_ep_registered"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
