import docker
import io

class SandboxEngine:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "agentic-sandbox-base:latest"
        self._prepare_secure_image()

    def _prepare_secure_image(self):
        """Builds a local Docker image with pytest pre-installed so we don't need internet at runtime."""
        dockerfile = """
        FROM python:3.11-slim
        RUN pip install --no-cache-dir pytest
        WORKDIR /workspace
        """
        print("[Sandbox] Verifying/Building secure base image with pytest...")
        try:
            self.client.images.build(
                fileobj=io.BytesIO(dockerfile.encode("utf-8")),
                tag=self.image_name,
                rm=True
            )
        except Exception as e:
            print(f"[Sandbox] Error building image: {e}")

    def run_validation(self, host_workspace_path: str) -> dict:
        try:
            container = self.client.containers.run(
                image=self.image_name,
                command="pytest --tb=short", # No pip install needed here anymore!
                volumes={host_workspace_path: {'bind': '/workspace', 'mode': 'rw'}},
                working_dir="/workspace",
                network_mode="none",         # Network remains completely disabled for safety
                mem_limit="512m",
                nano_cpus=1000000000,
                detach=True
            )
            
            result = container.wait(timeout=30)
            logs = container.logs().decode("utf-8")
            container.remove(force=True)
            
            return {
                "success": result["StatusCode"] == 0,
                "logs": logs
            }
        except Exception as e:
            return {"success": False, "logs": str(e)}