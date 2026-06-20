import os
import platform

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import (
    HOST_ARCH,
    OS_TYPE,
    OS_VERSION,
    SERVICE_NAME,
    Resource,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracing() -> None:
    # Define the service name resource for the tracer.
    resource = Resource(
        attributes={
            SERVICE_NAME: "backend",
            HOST_ARCH: platform.machine(),
            OS_TYPE: platform.system(),
            OS_VERSION: platform.version(),
        }
    )

    # Create a TracerProvider with the defined resource for creating tracers.
    provider = TracerProvider(resource=resource)

    # Configure the OTLP/HTTP Span Exporter with Axiom headers and endpoint.
    otlp_exporter = OTLPSpanExporter(
        endpoint="https://us-east-1.aws.edge.axiom.co/v1/traces",
        headers={
            "Authorization": f"Bearer {os.getenv('AXIOM_API_KEY')}",
            "X-Axiom-Dataset": os.getenv("AXIOM_DATASET_NAME", ""),
        },
    )

    # Create a BatchSpanProcessor with the OTLP exporter to batch and send trace spans.
    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)

    # Set the TracerProvider as the global tracer provider.
    trace.set_tracer_provider(provider)
