import { NextRequest, NextResponse } from "next/server";

const UNAUTHORIZED = new NextResponse("Authentication required", {
  status: 401,
  headers: { "WWW-Authenticate": 'Basic realm="giselle"' },
});

export function proxy(request: NextRequest) {
  const expectedUser = process.env.BASIC_AUTH_USER;
  const expectedPass = process.env.BASIC_AUTH_PASS;

  // If no credentials are configured, don't lock people out of local dev by accident.
  if (!expectedUser || !expectedPass) {
    return NextResponse.next();
  }

  const auth = request.headers.get("authorization");
  if (auth?.startsWith("Basic ")) {
    const [user, pass] = atob(auth.slice("Basic ".length)).split(":");
    if (user === expectedUser && pass === expectedPass) {
      return NextResponse.next();
    }
  }

  return UNAUTHORIZED;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
