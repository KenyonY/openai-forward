import streamlit as st
from streamlit.components.v1 import components


def mermaid(code: str) -> None:
    st.components.v1.html(
        f"""
            <pre class="mermaid">
                {code}
            </pre>

            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true }});
            </script>
            """,
        height=300,
    )
