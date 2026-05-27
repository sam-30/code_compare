import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi, describe, it, expect, beforeEach } from "vitest";
import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import RequireAuth from "../components/RequireAuth";
import * as authModule from "../api/auth";

// Mock authApi
vi.mock("../api/auth", async (importOriginal) => {
  const actual = await importOriginal<typeof authModule>();
  return {
    ...actual,
    authApi: {
      login: vi.fn(),
      register: vi.fn(),
      me: vi.fn(),
    },
  };
});

const mockAuthApi = authModule.authApi as {
  login: ReturnType<typeof vi.fn>;
  register: ReturnType<typeof vi.fn>;
  me: ReturnType<typeof vi.fn>;
};

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
});

// ---------------------------------------------------------------------------
// LoginPage
// ---------------------------------------------------------------------------

describe("LoginPage", () => {
  it("renders email and password inputs", () => {
    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="login" element={<LoginPage />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByTestId("email-input")).toBeInTheDocument();
    expect(screen.getByTestId("password-input")).toBeInTheDocument();
    expect(screen.getByTestId("submit-button")).toBeInTheDocument();
  });

  it("stores token and redirects on successful login", async () => {
    mockAuthApi.login.mockResolvedValue({
      access_token: "test-token-123",
      token_type: "bearer",
    });

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="login" element={<LoginPage />} />
          <Route path="/" element={<div data-testid="home">Home</div>} />
        </Routes>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByTestId("email-input"), {
      target: { value: "user@test.com" },
    });
    fireEvent.change(screen.getByTestId("password-input"), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByTestId("submit-button"));

    await waitFor(() =>
      expect(screen.getByTestId("home")).toBeInTheDocument()
    );
    expect(localStorage.getItem("access_token")).toBe("test-token-123");
  });

  it("shows error message on failed login", async () => {
    mockAuthApi.login.mockRejectedValue({
      response: { data: { detail: "Invalid credentials" } },
    });

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="login" element={<LoginPage />} />
        </Routes>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByTestId("email-input"), {
      target: { value: "bad@test.com" },
    });
    fireEvent.change(screen.getByTestId("password-input"), {
      target: { value: "wrongpass" },
    });
    fireEvent.click(screen.getByTestId("submit-button"));

    await waitFor(() =>
      expect(screen.getByTestId("error-message")).toBeInTheDocument()
    );
    expect(screen.getByTestId("error-message")).toHaveTextContent(
      "Invalid credentials"
    );
  });
});

// ---------------------------------------------------------------------------
// RegisterPage
// ---------------------------------------------------------------------------

describe("RegisterPage", () => {
  it("stores token and redirects on successful registration", async () => {
    mockAuthApi.register.mockResolvedValue({
      access_token: "new-token-456",
      token_type: "bearer",
    });

    render(
      <MemoryRouter initialEntries={["/register"]}>
        <Routes>
          <Route path="register" element={<RegisterPage />} />
          <Route path="/" element={<div data-testid="home">Home</div>} />
        </Routes>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByTestId("email-input"), {
      target: { value: "new@test.com" },
    });
    fireEvent.change(screen.getByTestId("password-input"), {
      target: { value: "longpassword" },
    });
    fireEvent.click(screen.getByTestId("submit-button"));

    await waitFor(() =>
      expect(screen.getByTestId("home")).toBeInTheDocument()
    );
    expect(localStorage.getItem("access_token")).toBe("new-token-456");
  });

  it("shows error on duplicate email", async () => {
    mockAuthApi.register.mockRejectedValue({
      response: { data: { detail: "Email already registered" } },
    });

    render(
      <MemoryRouter initialEntries={["/register"]}>
        <Routes>
          <Route path="register" element={<RegisterPage />} />
        </Routes>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByTestId("email-input"), {
      target: { value: "dup@test.com" },
    });
    fireEvent.change(screen.getByTestId("password-input"), {
      target: { value: "somepassword" },
    });
    fireEvent.click(screen.getByTestId("submit-button"));

    await waitFor(() =>
      expect(screen.getByTestId("error-message")).toBeInTheDocument()
    );
  });
});

// ---------------------------------------------------------------------------
// RequireAuth
// ---------------------------------------------------------------------------

describe("RequireAuth", () => {
  it("redirects to /login when no token is stored", () => {
    localStorage.removeItem("access_token");

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route element={<RequireAuth />}>
            <Route path="/" element={<div data-testid="protected">Protected</div>} />
          </Route>
          <Route path="login" element={<div data-testid="login-page">Login</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId("login-page")).toBeInTheDocument();
    expect(screen.queryByTestId("protected")).not.toBeInTheDocument();
  });

  it("renders children when token is present", () => {
    localStorage.setItem("access_token", "valid-token");

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route element={<RequireAuth />}>
            <Route path="/" element={<div data-testid="protected">Protected</div>} />
          </Route>
          <Route path="login" element={<div data-testid="login-page">Login</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId("protected")).toBeInTheDocument();
    expect(screen.queryByTestId("login-page")).not.toBeInTheDocument();
  });
});
