import { Switch, Route, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import NotFound from "@/pages/not-found";
import AuthPage from "@/pages/auth-page";
import Dashboard from "@/pages/dashboard";
import { useUser } from "@/hooks/use-user";
import { Loader2 } from "lucide-react";

function PrivateRoute({ component: Component, ...rest }: any) {
  const { user, isLoading } = useUser();
  const [, setLocation] = useLocation();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-border" />
      </div>
    );
  }

  if (!user) {
    setLocation('/auth');
    return null;
  }

  return <Component {...rest} />;
}

function Router() {
  const { user } = useUser();

  return (
    <Switch>
      <Route path="/auth">
        {() => user ? <Dashboard /> : <AuthPage />}
      </Route>
      <Route path="/dashboard">
        {() => <PrivateRoute component={Dashboard} />}
      </Route>
      <Route path="/">
        {() => <PrivateRoute component={Dashboard} />}
      </Route>
      <Route>
        {() => <NotFound />}
      </Route>
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router />
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;