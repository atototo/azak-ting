"use client";

import { useState, useEffect } from "react";
import ProtectedRoute from "@/app/components/ProtectedRoute";

/**
 * 사용자 타입
 */
interface User {
  id: number;
  email: string;
  nickname: string;
  role: "user" | "admin";
  is_active: boolean;
  expired_date: string | null;
  created_at: string;
  updated_at: string;
  report_update_enabled: boolean;
  report_update_quota: number;
  report_update_used: number;
}

/**
 * 사용자 생성 폼 데이터
 */
interface UserFormData {
  email: string;
  nickname: string;
  password: string;
  role: "user" | "admin";
  expired_date: string;
  report_update_enabled: boolean;
  report_update_quota: number;
}

/**
 * 관리자 전용 사용자 관리 페이지
 */
export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [showActionMenu, setShowActionMenu] = useState<number | null>(null);

  // 폼 데이터
  const [formData, setFormData] = useState<UserFormData>({
    email: "",
    nickname: "",
    password: "",
    role: "user",
    expired_date: "",
    report_update_enabled: false,
    report_update_quota: 0,
  });

  // 비밀번호 변경 폼
  const [newPassword, setNewPassword] = useState("");

  /**
   * 사용자 목록 조회
   */
  const fetchUsers = async () => {
    try {
      const response = await fetch("/api/users", {
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error("사용자 목록 조회 실패");
      }

      const data = await response.json();
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "오류가 발생했습니다");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  /**
   * 사용자 생성
   */
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      // expired_date를 ISO 형식으로 변환 (빈 값이면 null)
      // 로컬 시간대를 유지하면서 ISO 형식으로 변환
      const payload = {
        ...formData,
        expired_date: formData.expired_date
          ? formData.expired_date + ":00" // "2025-11-17T12:00" -> "2025-11-17T12:00:00"
          : null,
      };

      const response = await fetch("/api/users", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "사용자 생성 실패");
      }

      await fetchUsers();
      setShowCreateModal(false);
      setFormData({
        email: "",
        nickname: "",
        password: "",
        role: "user",
        expired_date: "",
        report_update_enabled: false,
        report_update_quota: 0,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "오류가 발생했습니다");
    }
  };

  /**
   * 사용자 수정
   */
  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;

    setError("");

    try {
      const updateData: any = {
        nickname: editingUser.nickname,
        role: editingUser.role,
        is_active: editingUser.is_active,
        expired_date: editingUser.expired_date
          ? (editingUser.expired_date.includes("T")
              ? editingUser.expired_date + ":00" // "2025-11-17T12:00" -> "2025-11-17T12:00:00"
              : editingUser.expired_date) // 이미 ISO 형식인 경우
          : null,
        report_update_enabled: editingUser.report_update_enabled,
        report_update_quota: editingUser.report_update_quota,
      };

      if (newPassword) {
        updateData.password = newPassword;
      }

      const response = await fetch(`/api/users/${editingUser.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "사용자 수정 실패");
      }

      await fetchUsers();
      setShowEditModal(false);
      setEditingUser(null);
      setNewPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "오류가 발생했습니다");
    }
  };

  /**
   * 사용자 삭제
   */
  const handleDeleteUser = async (userId: number) => {
    if (!confirm("정말로 이 사용자를 삭제하시겠습니까?")) {
      return;
    }

    try {
      const response = await fetch(`/api/users/${userId}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "사용자 삭제 실패");
      }

      await fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "오류가 발생했습니다");
    }
  };

  /**
   * 사용자 활성화/비활성화 토글
   */
  const handleToggleActive = async (user: User) => {
    try {
      const response = await fetch(`/api/users/${user.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ is_active: !user.is_active }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "사용자 상태 변경 실패");
      }

      await fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "오류가 발생했습니다");
    }
  };

  return (
    <ProtectedRoute requireAdmin>
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">사용자 관리</h1>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            + 사용자 추가
          </button>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">로딩 중...</p>
          </div>
        ) : (
          <>
            {/* 데스크톱 테이블 뷰 */}
            <div className="hidden md:block bg-white shadow-md rounded-lg overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    이메일
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    닉네임
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    역할
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    상태
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    리포트 할당량
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    유효기간
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    가입일
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    작업
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {user.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {user.nickname}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          user.role === "admin"
                            ? "bg-blue-100 text-blue-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {user.role === "admin" ? "관리자" : "사용자"}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          user.is_active
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {user.is_active ? "활성" : "비활성"}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {user.role === "admin" ? (
                        <span className="text-blue-600 font-semibold">무제한</span>
                      ) : user.report_update_enabled ? (
                        <span className={
                          user.report_update_used >= user.report_update_quota
                            ? "text-red-600"
                            : "text-green-600"
                        }>
                          {user.report_update_used} / {user.report_update_quota}
                        </span>
                      ) : (
                        <span className="text-gray-400">권한 없음</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.expired_date ? (
                        <span className={
                          new Date(user.expired_date) < new Date()
                            ? "text-red-600 font-semibold"
                            : "text-gray-700"
                        }>
                          {new Date(user.expired_date).toLocaleDateString("ko-KR")}
                        </span>
                      ) : (
                        <span className="text-blue-600">무제한</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(user.created_at).toLocaleDateString("ko-KR")}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="relative inline-block">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setShowActionMenu(showActionMenu === user.id ? null : user.id);
                          }}
                          className="text-gray-400 hover:text-gray-600 p-2"
                        >
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/>
                          </svg>
                        </button>
                        {showActionMenu === user.id && (
                          <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                            <div className="py-1">
                              <button
                                onClick={() => {
                                  setEditingUser(user);
                                  setShowEditModal(true);
                                  setShowActionMenu(null);
                                }}
                                className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-blue-50"
                              >
                                ✏️ 수정
                              </button>
                              <button
                                onClick={() => {
                                  handleToggleActive(user);
                                  setShowActionMenu(null);
                                }}
                                className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-yellow-50"
                              >
                                🔄 {user.is_active ? "비활성화" : "활성화"}
                              </button>
                              <button
                                onClick={() => {
                                  handleDeleteUser(user.id);
                                  setShowActionMenu(null);
                                }}
                                className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                              >
                                🗑️ 삭제
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 모바일 카드 뷰 */}
          <div className="md:hidden space-y-4">
            {users.map((user) => (
              <div key={user.id} className="bg-white shadow-md rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{user.nickname}</h3>
                    <p className="text-sm text-gray-600">{user.email}</p>
                  </div>
                  <div className="flex gap-2">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      user.role === "admin" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-800"
                    }`}>
                      {user.role === "admin" ? "관리자" : "사용자"}
                    </span>
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      user.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                    }`}>
                      {user.is_active ? "활성" : "비활성"}
                    </span>
                  </div>
                </div>

                <div className="space-y-2 text-sm mb-4">
                  <div className="flex justify-between">
                    <span className="text-gray-600">유효기간:</span>
                    <span className={user.expired_date && new Date(user.expired_date) < new Date() ? "text-red-600 font-semibold" : "text-gray-900"}>
                      {user.expired_date ? new Date(user.expired_date).toLocaleDateString("ko-KR") : <span className="text-blue-600">무제한</span>}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">리포트 할당량:</span>
                    <span>
                      {user.role === "admin" ? (
                        <span className="text-blue-600 font-semibold">무제한</span>
                      ) : user.report_update_enabled ? (
                        <span className={
                          user.report_update_used >= user.report_update_quota
                            ? "text-red-600 font-semibold"
                            : "text-green-600"
                        }>
                          {user.report_update_used} / {user.report_update_quota}
                        </span>
                      ) : (
                        <span className="text-gray-400">권한 없음</span>
                      )}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">가입일:</span>
                    <span className="text-gray-900">{new Date(user.created_at).toLocaleDateString("ko-KR")}</span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => {
                      setEditingUser(user);
                      setShowEditModal(true);
                    }}
                    className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
                  >
                    ✏️ 수정
                  </button>
                  <button
                    onClick={() => handleToggleActive(user)}
                    className="px-3 py-2 bg-yellow-500 text-white rounded-md hover:bg-yellow-600 transition-colors text-sm"
                  >
                    🔄
                  </button>
                  <button
                    onClick={() => handleDeleteUser(user.id)}
                    className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
          </>
        )}

        {/* 사용자 생성 모달 */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <h3 className="text-lg font-medium text-gray-900 mb-4">사용자 추가</h3>
              <form onSubmit={handleCreateUser} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    이메일
                  </label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    닉네임
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.nickname}
                    onChange={(e) => setFormData({ ...formData, nickname: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    비밀번호 (8자 이상)
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">역할</label>
                  <select
                    value={formData.role}
                    onChange={(e) =>
                      setFormData({ ...formData, role: e.target.value as "user" | "admin" })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="user">사용자</option>
                    <option value="admin">관리자</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    유효기간 (선택사항)
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.expired_date || ""}
                    onChange={(e) => {
                      console.log("Selected datetime:", e.target.value);
                      setFormData({ ...formData, expired_date: e.target.value });
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    비워두면 무제한으로 설정됩니다
                  </p>
                  {formData.expired_date && (
                    <p className="mt-1 text-xs text-blue-600">
                      선택된 값: {formData.expired_date}
                    </p>
                  )}
                </div>

                {/* 리포트 업데이트 권한 설정 (사용자만) */}
                {formData.role === "user" && (
                  <>
                    <div className="border-t pt-4">
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={formData.report_update_enabled}
                          onChange={(e) =>
                            setFormData({ ...formData, report_update_enabled: e.target.checked })
                          }
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-700">
                          리포트 업데이트 권한 부여
                        </span>
                      </label>
                    </div>
                    {formData.report_update_enabled && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          리포트 업데이트 할당 횟수
                        </label>
                        <input
                          type="number"
                          min="0"
                          value={formData.report_update_quota}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              report_update_quota: parseInt(e.target.value) || 0,
                            })
                          }
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="mt-1 text-xs text-gray-500">
                          0으로 설정하면 업데이트 불가능
                        </p>
                      </div>
                    )}
                  </>
                )}
                <div className="flex justify-end space-x-2 mt-6">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateModal(false);
                      setFormData({
                        email: "",
                        nickname: "",
                        password: "",
                        role: "user",
                        expired_date: "",
                        report_update_enabled: false,
                        report_update_quota: 0,
                      });
                    }}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
                  >
                    취소
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    생성
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* 사용자 수정 모달 */}
        {showEditModal && editingUser && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <h3 className="text-lg font-medium text-gray-900 mb-4">사용자 수정</h3>
              <form onSubmit={handleUpdateUser} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    이메일 (변경 불가)
                  </label>
                  <input
                    type="email"
                    disabled
                    value={editingUser.email}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    닉네임
                  </label>
                  <input
                    type="text"
                    required
                    value={editingUser.nickname}
                    onChange={(e) =>
                      setEditingUser({ ...editingUser, nickname: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    새 비밀번호 (선택사항, 8자 이상)
                  </label>
                  <input
                    type="password"
                    minLength={8}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="변경하지 않으려면 비워두세요"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">역할</label>
                  <select
                    value={editingUser.role}
                    onChange={(e) =>
                      setEditingUser({ ...editingUser, role: e.target.value as "user" | "admin" })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="user">사용자</option>
                    <option value="admin">관리자</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    유효기간 (선택사항)
                  </label>
                  <input
                    type="datetime-local"
                    value={
                      editingUser.expired_date
                        ? (() => {
                            try {
                              // ISO 형식 문자열을 datetime-local 형식으로 변환
                              // "2025-11-17T12:00:00" -> "2025-11-17T12:00"
                              const dateStr = editingUser.expired_date.slice(0, 16);
                              return dateStr;
                            } catch {
                              return "";
                            }
                          })()
                        : ""
                    }
                    onChange={(e) => {
                      console.log("Edit - Selected datetime:", e.target.value);
                      setEditingUser({ ...editingUser, expired_date: e.target.value || null });
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    비워두면 무제한으로 설정됩니다
                  </p>
                </div>

                {/* 리포트 업데이트 권한 설정 (사용자만) */}
                {editingUser.role === "user" && (
                  <>
                    <div className="border-t pt-4">
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={editingUser.report_update_enabled}
                          onChange={(e) =>
                            setEditingUser({
                              ...editingUser,
                              report_update_enabled: e.target.checked,
                            })
                          }
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-700">
                          리포트 업데이트 권한 부여
                        </span>
                      </label>
                    </div>
                    {editingUser.report_update_enabled && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          리포트 업데이트 할당 횟수
                        </label>
                        <input
                          type="number"
                          min="0"
                          value={editingUser.report_update_quota}
                          onChange={(e) =>
                            setEditingUser({
                              ...editingUser,
                              report_update_quota: parseInt(e.target.value) || 0,
                            })
                          }
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="mt-1 text-xs text-gray-500">
                          사용 중: {editingUser.report_update_used}회 / 총 할당: {editingUser.report_update_quota}회
                        </p>
                      </div>
                    )}
                  </>
                )}
                <div className="flex justify-end space-x-2 mt-6">
                  <button
                    type="button"
                    onClick={() => {
                      setShowEditModal(false);
                      setEditingUser(null);
                      setNewPassword("");
                    }}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
                  >
                    취소
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    수정
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
