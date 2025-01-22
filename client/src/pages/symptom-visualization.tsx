import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Activity, AlertCircle, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface SymptomDataPoint {
  timestamp: string;
  name: string;
  intensity: number;
}

interface AIInsight {
  trends: string[];
  recommendations: string[];
}

interface SymptomJourneyResponse {
  symptomHistory: SymptomDataPoint[];
  insights: AIInsight;
}

export default function SymptomVisualization() {
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'year'>('week');

  const { data, isLoading, error } = useQuery<SymptomJourneyResponse>({
    queryKey: ['/api/symptom-journey', { timeRange }],
    queryFn: async () => {
      const response = await fetch(`/api/symptom-journey?timeRange=${timeRange}`);
      if (!response.ok) {
        throw new Error('Failed to fetch symptom data');
      }
      return response.json();
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-secondary rounded w-32"></div>
          <div className="h-64 bg-secondary rounded w-full max-w-3xl"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          Failed to load symptom data. Please try again later.
        </AlertDescription>
      </Alert>
    );
  }

  const symptoms = data?.symptomHistory || [];
  const insights = data?.insights || { trends: [], recommendations: [] };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Symptom Journey</h1>
        <Select
          value={timeRange}
          onValueChange={(value: 'week' | 'month' | 'year') => setTimeRange(value)}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select time range" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="week">Past Week</SelectItem>
            <SelectItem value="month">Past Month</SelectItem>
            <SelectItem value="year">Past Year</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Symptom Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" />
              Symptom Progression
            </CardTitle>
            <CardDescription>
              Track your symptoms intensity over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={symptoms}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(timestamp) => new Date(timestamp).toLocaleDateString()}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(timestamp) => new Date(timestamp).toLocaleString()}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="intensity"
                    name="Symptom Intensity"
                    stroke="hsl(var(--primary))"
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* AI Insights */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              AI Insights
            </CardTitle>
            <CardDescription>
              AI-powered analysis of your symptoms
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <h3 className="font-semibold mb-2">Trends</h3>
                <ul className="space-y-2">
                  {insights.trends.map((trend, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <AlertCircle className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                      {trend}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Recommendations</h3>
                <ul className="space-y-2">
                  {insights.recommendations.map((recommendation, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <AlertCircle className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                      {recommendation}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
