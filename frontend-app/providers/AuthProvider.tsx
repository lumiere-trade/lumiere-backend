'use client';

/**
 * Auth Provider.
 * Manages authentication state and operations.
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
} from 'react';
import { useRouter } from 'next/navigation';
import { container } from '@/lib/infrastructure/di/container';
import { User } from '@/lib/domain/entities/user.entity';
import { PendingDocument } from '@/lib/domain/entities/pending-document.entity';
import { LegalDocument } from '@/lib/domain/entities/legal-document.entity';
import { AuthError } from '@/lib/domain/errors/auth.errors';
import { ROUTES } from '@/config/constants';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  pendingDocuments: PendingDocument[];
  legalDocuments: LegalDocument[];
  error: string | null;

  login: () => Promise<void>;
  createAccount: (acceptedDocumentIds: string[]) => Promise<void>;
  logout: () => void;
  acceptPendingDocuments: (documentIds: string[]) => Promise<void>;
  checkCompliance: () => Promise<void>;
  loadLegalDocuments: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [pendingDocuments, setPendingDocuments] = useState<PendingDocument[]>([]);
  const [legalDocuments, setLegalDocuments] = useState<LegalDocument[]>([]);
  const [error, setError] = useState<string | null>(null);

  const router = useRouter();
  const initRef = useRef(false);

  const authService = container.authService;
  const legalService = container.legalService;

  const loadLegalDocuments = useCallback(async () => {
    try {
      const docs = await legalService.getActiveLegalDocuments();
      setLegalDocuments(docs);
    } catch (err) {
      console.error('Failed to load legal documents:', err);
    }
  }, [legalService]);

  const checkCompliance = useCallback(async () => {
    try {
      const missing = await authService.checkCompliance();
      setPendingDocuments(missing);
    } catch (err) {
      console.error('Failed to check compliance:', err);
    }
  }, [authService]);

  const refreshUser = useCallback(async () => {
    try {
      if (authService.isAuthenticated()) {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
        setPendingDocuments(
          currentUser.pendingDocuments.map((doc) =>
            PendingDocument.fromApi({
              id: doc.id,
              document_type: doc.documentType,
              version: doc.version,
              title: doc.title,
              content: doc.content,
              status: doc.status,
              effective_date: doc.effectiveDate.toISOString(),
              created_at: doc.createdAt.toISOString(),
              updated_at: doc.updatedAt.toISOString(),
            })
          )
        );
      }
    } catch (err) {
      console.error('Failed to refresh user:', err);
    }
  }, [authService]);

  useEffect(() => {
    const initAuth = async () => {
      if (initRef.current) return;
      initRef.current = true;

      if (authService.isAuthenticated()) {
        try {
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
          setPendingDocuments(
            currentUser.pendingDocuments.map((doc) =>
              PendingDocument.fromApi({
                id: doc.id,
                document_type: doc.documentType,
                version: doc.version,
                title: doc.title,
                content: doc.content,
                status: doc.status,
                effective_date: doc.effectiveDate.toISOString(),
                created_at: doc.createdAt.toISOString(),
                updated_at: doc.updatedAt.toISOString(),
              })
            )
          );
        } catch (err) {
          authService.logout();
        }
      }

      setIsLoading(false);
    };

    initAuth();
  }, [authService]);

  const login = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await authService.verifyAndLogin();

      setUser(result.user);
      setPendingDocuments(result.pendingDocuments);

      if (result.pendingDocuments.length > 0) {
        router.push('/onboarding');
      } else {
        router.push(ROUTES.DASHBOARD);
      }
    } catch (err) {
      const errorMessage =
        err instanceof AuthError
          ? err.message
          : 'Authentication failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [authService, router]);

  const createAccount = useCallback(
    async (acceptedDocumentIds: string[]) => {
      setIsLoading(true);
      setError(null);

      try {
        const result = await authService.createAccount(acceptedDocumentIds);

        setUser(result.user);
        setPendingDocuments([]);

        router.push(ROUTES.DASHBOARD);
      } catch (err) {
        const errorMessage =
          err instanceof AuthError
            ? err.message
            : 'Account creation failed';
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [authService, router]
  );

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
    setPendingDocuments([]);
    setError(null);
    router.push(ROUTES.HOME);
  }, [authService, router]);

  const acceptPendingDocuments = useCallback(
    async (documentIds: string[]) => {
      setError(null);

      try {
        await authService.acceptPendingDocuments(documentIds);

        const updatedUser = await authService.getCurrentUser();
        setUser(updatedUser);
        setPendingDocuments(
          updatedUser.pendingDocuments.map((doc) =>
            PendingDocument.fromApi({
              id: doc.id,
              document_type: doc.documentType,
              version: doc.version,
              title: doc.title,
              content: doc.content,
              status: doc.status,
              effective_date: doc.effectiveDate.toISOString(),
              created_at: doc.createdAt.toISOString(),
              updated_at: doc.updatedAt.toISOString(),
            })
          )
        );
      } catch (err) {
        const errorMessage =
          err instanceof Error
            ? err.message
            : 'Failed to accept documents';
        setError(errorMessage);
        throw err;
      }
    },
    [authService]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        isLoading,
        pendingDocuments,
        legalDocuments,
        error,
        login,
        createAccount,
        logout,
        acceptPendingDocuments,
        checkCompliance,
        loadLegalDocuments,
        refreshUser,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
