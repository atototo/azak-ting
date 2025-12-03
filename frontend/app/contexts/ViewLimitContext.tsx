"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import { useAuth } from "./AuthContext";

/**
 * 하루 무료 조회 제한 수
 */
const DAILY_VIEW_LIMIT = 3;

/**
 * localStorage 키
 */
const STORAGE_KEY = "azak_view_limit";

/**
 * 저장 데이터 타입
 */
interface StoredViewData {
  date: string;        // YYYY-MM-DD 형식
  viewedStocks: string[]; // 조회한 종목 코드 목록
}

/**
 * ViewLimit 컨텍스트 타입
 */
interface ViewLimitContextType {
  /** 남은 무료 조회 횟수 */
  remainingViews: number;
  /** 오늘 조회한 종목 수 */
  viewedCount: number;
  /** 일일 제한 수 */
  dailyLimit: number;
  /** 제한에 도달했는지 여부 */
  isLimitReached: boolean;
  /** 종목 조회 가능 여부 체크 (이미 본 종목은 다시 볼 수 있음) */
  canViewStock: (stockCode: string) => boolean;
  /** 종목 조회 기록 (조회 횟수 증가) */
  recordView: (stockCode: string) => boolean;
  /** 후원 모달 표시 여부 */
  showDonationModal: boolean;
  /** 후원 모달 닫기 */
  closeDonationModal: () => void;
  /** 후원 모달 열기 */
  openDonationModal: () => void;
}

/**
 * ViewLimit 컨텍스트 생성
 */
const ViewLimitContext = createContext<ViewLimitContextType | undefined>(undefined);

/**
 * 오늘 날짜를 YYYY-MM-DD 형식으로 반환
 */
function getTodayString(): string {
  const today = new Date();
  return today.toISOString().split("T")[0];
}

/**
 * localStorage에서 조회 데이터 가져오기
 */
function getStoredData(): StoredViewData {
  if (typeof window === "undefined") {
    return { date: getTodayString(), viewedStocks: [] };
  }

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const data: StoredViewData = JSON.parse(stored);
      // 날짜가 다르면 리셋
      if (data.date !== getTodayString()) {
        return { date: getTodayString(), viewedStocks: [] };
      }
      return data;
    }
  } catch (error) {
    console.error("Failed to parse view limit data:", error);
  }

  return { date: getTodayString(), viewedStocks: [] };
}

/**
 * localStorage에 조회 데이터 저장
 */
function saveStoredData(data: StoredViewData): void {
  if (typeof window === "undefined") return;

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.error("Failed to save view limit data:", error);
  }
}

/**
 * ViewLimit 컨텍스트 프로바이더 Props
 */
interface ViewLimitProviderProps {
  children: ReactNode;
}

/**
 * ViewLimit 컨텍스트 프로바이더
 *
 * 비로그인 사용자의 하루 종목 상세 조회 횟수를 제한합니다.
 * - 하루 3건까지 무료 조회 가능
 * - 로그인한 사용자는 제한 없음
 * - 날짜가 바뀌면 카운터 리셋
 * - 이미 본 종목은 다시 봐도 카운터 증가 안 함
 */
export function ViewLimitProvider({ children }: ViewLimitProviderProps) {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [viewedStocks, setViewedStocks] = useState<string[]>([]);
  const [showDonationModal, setShowDonationModal] = useState(false);
  const [initialized, setInitialized] = useState(false);

  // 초기화: localStorage에서 데이터 로드
  useEffect(() => {
    const data = getStoredData();
    setViewedStocks(data.viewedStocks);
    setInitialized(true);
  }, []);

  // viewedStocks 변경 시 localStorage 저장
  useEffect(() => {
    if (initialized) {
      saveStoredData({
        date: getTodayString(),
        viewedStocks,
      });
    }
  }, [viewedStocks, initialized]);

  // 계산된 값들
  const viewedCount = viewedStocks.length;
  const remainingViews = Math.max(0, DAILY_VIEW_LIMIT - viewedCount);
  const isLimitReached = viewedCount >= DAILY_VIEW_LIMIT;

  /**
   * 종목 조회 가능 여부 체크
   * - 로그인 사용자: 항상 가능
   * - 이미 본 종목: 가능
   * - 제한 미도달: 가능
   */
  const canViewStock = useCallback((stockCode: string): boolean => {
    // 인증 로딩 중이면 일단 허용
    if (authLoading) return true;

    // 로그인한 사용자는 제한 없음
    if (isAuthenticated) return true;

    // 이미 본 종목은 다시 볼 수 있음
    if (viewedStocks.includes(stockCode)) return true;

    // 제한에 도달했으면 불가
    return !isLimitReached;
  }, [isAuthenticated, authLoading, viewedStocks, isLimitReached]);

  /**
   * 종목 조회 기록
   * @returns 조회 성공 여부
   */
  const recordView = useCallback((stockCode: string): boolean => {
    // 로그인한 사용자는 기록하지 않음
    if (isAuthenticated) return true;

    // 이미 본 종목은 카운터 증가 안 함
    if (viewedStocks.includes(stockCode)) return true;

    // 제한에 도달했으면 모달 표시하고 실패 반환
    if (isLimitReached) {
      setShowDonationModal(true);
      return false;
    }

    // 새 종목 추가
    setViewedStocks(prev => [...prev, stockCode]);

    // 이번 조회로 제한에 도달하면 다음에 모달 표시 준비
    if (viewedCount + 1 >= DAILY_VIEW_LIMIT) {
      // 마지막 무료 조회 - 아직 모달 표시 안 함
    }

    return true;
  }, [isAuthenticated, viewedStocks, isLimitReached, viewedCount]);

  const closeDonationModal = useCallback(() => {
    setShowDonationModal(false);
  }, []);

  const openDonationModal = useCallback(() => {
    setShowDonationModal(true);
  }, []);

  const value: ViewLimitContextType = {
    remainingViews,
    viewedCount,
    dailyLimit: DAILY_VIEW_LIMIT,
    isLimitReached,
    canViewStock,
    recordView,
    showDonationModal,
    closeDonationModal,
    openDonationModal,
  };

  return (
    <ViewLimitContext.Provider value={value}>
      {children}
    </ViewLimitContext.Provider>
  );
}

/**
 * ViewLimit 컨텍스트 Hook
 */
export function useViewLimit(): ViewLimitContextType {
  const context = useContext(ViewLimitContext);
  if (context === undefined) {
    throw new Error("useViewLimit must be used within a ViewLimitProvider");
  }
  return context;
}
