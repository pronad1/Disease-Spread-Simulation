export default {
	// Optional: manual fetch endpoint
	async fetch(_req: Request, env: Env): Promise<Response> {
		const r = await ping(env.PING_URL);
		return new Response(JSON.stringify(r), {
			headers: { "content-type": "application/json" }
		});
	},

	// Cron job: runs automatically on schedule
	async scheduled(_event: ScheduledEvent, env: Env, _ctx: ExecutionContext) {
		await ping(env.PING_URL);
	}
};

type Env = {
	PING_URL: string;
};

async function ping(url: string) {
	const started = Date.now();
	try {
		const res = await fetch(url, { method: "GET", cache: "no-store" });
		const ms = Date.now() - started;
		return { ok: res.ok, status: res.status, ms };
	} catch (e: any) {
		const ms = Date.now() - started;
		return { ok: false, error: e?.message || String(e), ms };
	}
}
