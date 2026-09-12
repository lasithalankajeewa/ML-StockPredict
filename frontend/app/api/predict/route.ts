import { NextResponse } from "next/server";

const fastApiUrl = process.env.FASTAPI_URL ?? "http://127.0.0.1:8000";

export async function POST(request: Request) {
  try {
    const payload = await request.json();
    const response = await fetch(`${fastApiUrl}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
    });
    const body = await response.json();
    return NextResponse.json(body, { status: response.status });
  } catch {
    return NextResponse.json(
      { detail: "FastAPI is unavailable. Start it on port 8000 and try again." },
      { status: 502 },
    );
  }
}
