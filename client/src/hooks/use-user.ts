import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

type User = {
  id: number;
  username: string;
  email: string;
  name: string;
  role: string;
  specialty?: string | null;
}

async function handleAuthRequest(
  url: string,
  method: string,
  body?: { username: string; password: string }
): Promise<User> {
  const response = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    credentials: "include",
  });

  if (!response.ok) {
    const data = await response.text();
    throw new Error(data || response.statusText);
  }

  return response.json();
}

async function fetchUser(): Promise<User | null> {
  try {
    const response = await fetch('/api/auth/user', {
      credentials: 'include'
    });

    if (!response.ok) {
      if (response.status === 401) {
        return null;
      }
      throw new Error(await response.text());
    }

    return response.json();
  } catch (error) {
    console.error('Error fetching user:', error);
    return null;
  }
}

export function useUser() {
  const queryClient = useQueryClient();

  const { data: user, error, isLoading } = useQuery<User | null>({
    queryKey: ['/api/auth/user'],
    queryFn: fetchUser,
    staleTime: Infinity,
    retry: false
  });

  const loginMutation = useMutation({
    mutationFn: (credentials: { username: string; password: string }) => 
      handleAuthRequest('/api/auth/login', 'POST', credentials),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/auth/user'] });
    },
  });

  const logoutMutation = useMutation({
    mutationFn: () => handleAuthRequest('/api/auth/logout', 'POST'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/auth/user'] });
    },
  });

  return {
    user,
    isLoading: isLoading || loginMutation.isPending || logoutMutation.isPending,
    error,
    login: loginMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
  };
}