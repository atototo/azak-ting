import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * 퍼블릭 접근 허용 경로
 * 로그인 없이도 접근 가능한 페이지
 */
const PUBLIC_PATHS = [
  "/",           // 대시보드
  "/stocks",     // 종목 목록
];

/**
 * 퍼블릭 접근 허용 경로 프리픽스
 * 하위 경로 포함 (예: /stocks/005930)
 */
const PUBLIC_PATH_PREFIXES = [
  "/stocks/",    // 종목 상세 페이지
];

/**
 * Next.js 미들웨어 - 인증 및 권한 체크
 *
 * 모든 요청을 가로채서 인증 상태를 확인하고,
 * 비인증 사용자를 로그인 페이지로 리다이렉트합니다.
 *
 * 단, 퍼블릭 경로(대시보드, 종목 목록/상세)는 로그인 없이 접근 가능합니다.
 */
export async function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;

  // 로그인 페이지와 API 엔드포인트는 체크하지 않음
  if (pathname === "/login" || pathname.startsWith("/api/")) {
    return NextResponse.next();
  }

  // 퍼블릭 경로는 인증 없이 통과
  if (PUBLIC_PATHS.includes(pathname)) {
    return NextResponse.next();
  }

  // 퍼블릭 경로 프리픽스 체크 (하위 경로 포함)
  if (PUBLIC_PATH_PREFIXES.some(prefix => pathname.startsWith(prefix))) {
    return NextResponse.next();
  }

  // 프리뷰 URL 처리 (블로그 캡처용)
  if (pathname.startsWith("/preview/")) {
    const token = searchParams.get("token");
    const validToken = process.env.PREVIEW_TOKEN;

    // 토큰 검증
    if (!token || !validToken || token !== validToken) {
      return new NextResponse("Unauthorized: Invalid preview token", { status: 401 });
    }

    // 토큰이 유효하면 통과 (인증 우회)
    return NextResponse.next();
  }

  // 공개 프리뷰 URL 처리 (홍보용 공개 링크)
  if (pathname.startsWith("/public/")) {
    // 인증 없이 통과
    return NextResponse.next();
  }

  // 공개 프리뷰 모드 체크 (isPublicPreview 쿼리 파라미터)
  const isPublicPreview = searchParams.get("isPublicPreview");
  if (isPublicPreview === "true") {
    // 인증 없이 통과
    return NextResponse.next();
  }

  // 세션 쿠키 확인
  const sessionCookie = request.cookies.get("azak_session");

  // 세션이 없으면 로그인 페이지로 리다이렉트
  if (!sessionCookie) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // 세션 쿠키가 있으면 일단 통과
  // 실제 인증 확인은 각 페이지나 API에서 수행
  return NextResponse.next();
}

/**
 * 미들웨어가 실행될 경로 설정
 */
export const config = {
  matcher: [
    /*
     * 다음 경로를 제외한 모든 요청에 미들웨어 적용:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};
