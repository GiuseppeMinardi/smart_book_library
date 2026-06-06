import os

from openinference.instrumentation.pydantic_ai import OpenInferenceSpanProcessor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


def setup_phoenix_tracing():
    # Set up the tracer provider

    tracer_provider = TracerProvider()
    trace.set_tracer_provider(tracer_provider)

    phoenix_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    phoenix_api_key = os.environ.get("PHOENIX_API_KEY")
    if not phoenix_endpoint:
        raise ValueError("⚠️ Warning: PHOENIX_COLLECTOR_ENDPOINT is not set. Traces will not be sent to Phoenix.")
    # if not phoenix_api_key:
    #     raise ValueError("⚠️ Warning: PHOENIX_API_KEY is not set. Traces will not be sent to Phoenix.")

    # Add the OpenInference span processor
    endpoint = f"{os.environ['PHOENIX_COLLECTOR_ENDPOINT']}/v1/traces"

    # If you are using a local instance without auth, ignore these headers
    # headers = {"Authorization": f"Bearer {os.environ['PHOENIX_API_KEY']}"}
    exporter = OTLPSpanExporter(
        endpoint=endpoint, 
        # headers=headers
    )

    tracer_provider.add_span_processor(OpenInferenceSpanProcessor())
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))