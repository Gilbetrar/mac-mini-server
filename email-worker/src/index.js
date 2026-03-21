export default {
  async email(message, env, ctx) {
    const rawEmail = new Response(message.raw);
    const body = await rawEmail.arrayBuffer();

    const response = await fetch(env.WEBHOOK_URL, {
      method: "POST",
      headers: {
        "Content-Type": "message/rfc822",
        "X-Webhook-Secret": env.WEBHOOK_SECRET,
        "X-Original-From": message.from,
        "X-Original-To": message.to,
      },
      body: body,
    });

    if (!response.ok) {
      message.setReject(`Webhook returned ${response.status}`);
    }
  },
};
