import { useState, useEffect } from "react";
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";

interface SymptomData {
  timestamp: string;
  intensity: number;
  name: string;
  notes?: string;
}

interface SymptomJourney {
  symptomHistory: SymptomData[];
  insights: {
    trends: string[];
    recommendations: string[];
  };
}

export default function SymptomJourney() {
  const [timeRange, setTimeRange] = useState<string>("week");
  const [selectedSymptom, setSelectedSymptom] = useState<string>("all");

  const { data: journeyData, isLoading } = useQuery<SymptomJourney>({
    queryKey: ["/api/symptom-journey", timeRange, selectedSymptom],
  });

  const formatChartData = (data: SymptomData[] | undefined) => {
    if (!data) return [];
    
    // Group data by date and symptom
    const groupedData = data.reduce((acc: any, curr) => {
      const date = new Date(curr.timestamp).toLocaleDateString();
      if (!acc[date]) {
        acc[date] = { date };
      }
      acc[date][curr.name] = curr.intensity;
      return acc;
    }, {});

    return Object.values(groupedData);
  };

  const getSymptomColor = (symptomName: string) => {
    const colors: { [key: string]: string } = {
      fever: "#ef4444",
      cough: "#f97316",
      fatigue: "#facc15",
      default: "#8b5cf6",
    };
    return colors[symptomName.toLowerCase()] || colors.default;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const chartData = formatChartData(journeyData?.symptomHistory);
  const uniqueSymptoms = Array.from(
    new Set(journeyData?.symptomHistory.map((s) => s.name) || [])
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold tracking-tight">Symptom Journey</h2>
          <p className="text-muted-foreground">
            Track your symptom progression over time
          </p>
        </div>
        <div className="flex space-x-2">
          <Select value={selectedSymptom} onValueChange={setSelectedSymptom}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select symptom" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Symptoms</SelectItem>
              {uniqueSymptoms.map((symptom) => (
                <SelectItem key={symptom} value={symptom}>
                  {symptom}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={timeRange} onValueChange={setTimeRange}>
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
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Symptom Intensity Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[0, 10]} />
                <Tooltip />
                <Legend />
                {(selectedSymptom === "all" ? uniqueSymptoms : [selectedSymptom]).map(
                  (symptom) => (
                    <Line
                      key={symptom}
                      type="monotone"
                      dataKey={symptom}
                      name={symptom}
                      stroke={getSymptomColor(symptom)}
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  )
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {journeyData?.insights && (
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>AI Insights</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {journeyData.insights.trends.map((trend, i) => (
                  <li key={i} className="text-sm text-muted-foreground">
                    • {trend}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {journeyData.insights.recommendations.map((rec, i) => (
                  <li key={i} className="text-sm text-muted-foreground">
                    • {rec}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
