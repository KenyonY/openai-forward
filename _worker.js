export default {
    async fetch(request, env) {
        try {
            const url = new URL(request.url);
            url.hostname = "api.openai.com";
            return await fetch(
                new Request(url, {method: request.method, headers: request.headers, body: request.body})
            );
        } catch (e) {
            return new Response(e.stack, {status: 500});
        }
    }
}
