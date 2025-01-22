import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

type User = {
  id: number;
  username: string;
  email: string;
  name: string;
  role: string;
  specialty?: string | null;
}

async function handleRequest(
  url: string,
  method: string,
  body?: { username: string; password: string }
): Promise<{ message?: string; error?: string }> {
  try {
    const response = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      credentials: "include",
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || response.statusText);
    }

    return data;
  } catch (error: any) {
    throw new Error(error.message || 'An error occurred');
  }
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
      handleRequest('/api/auth/login', 'POST', credentials),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/auth/user'] });
    },
  });

  const logoutMutation = useMutation({
    mutationFn: () => handleRequest('/api/auth/logout', 'POST'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/auth/user'] });
    },
  });

  return {
    user,
    isLoading,
    error,
    login: loginMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
  };
}