export default {
    async fetch(request, env) {
        try {
            const OPENAI_API_HOST = "api.openai.com";
            const url = new URL(request.url);
            url.hostname = OPENAI_API_HOST;
            const newRequest = new Request(
                url, {
                    method: request.method,
                    headers: request.headers,
                    body: request.body
                });
            return await fetch(newRequest);
        } catch (e) {
            return new Response(e.stack, {status: 500});
        }
    }
}
