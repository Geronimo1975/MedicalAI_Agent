import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  BarChart,
  Bar,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertTriangle } from "lucide-react";

interface RiskData {
  symptom: string;
  risk: number;
  severity: number;
  correlation: number;
}

interface RiskAssessment {
  total_risk: number;
  severity_score: number;
  correlation_score: number;
  risk_multiplier: number;
  symptoms: RiskData[];
  recommendations: string;
}

export default function RiskVisualizer() {
  const [selectedMetric, setSelectedMetric] = useState<string>("risk");
  const [timeRange, setTimeRange] = useState<string>("week");

  const { data: riskAssessment, isLoading } = useQuery<RiskAssessment>({
    queryKey: ["/api/risk-assessment", timeRange],
  });

  const formatRiskData = (assessment: RiskAssessment | undefined) => {
    if (!assessment) return [];
    return assessment.symptoms.map((symptom) => ({
      name: symptom.symptom,
      risk: symptom.risk * 10,
      severity: symptom.severity * 10,
      correlation: symptom.correlation * 10,
    }));
  };

  const getChartColor = (riskScore: number) => {
    if (riskScore >= 8) return "#ef4444"; // Red
    if (riskScore >= 6) return "#f97316"; // Orange
    if (riskScore >= 4) return "#facc15"; // Yellow
    return "#22c55e"; // Green
  };

  const renderSeverityAlert = (risk: number) => {
    if (risk >= 8) {
      return (
        <Alert variant="destructive" className="mt-4">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>High Risk Level Detected</AlertTitle>
          <AlertDescription>
            Your risk level is significantly elevated. Please seek immediate medical attention.
          </AlertDescription>
        </Alert>
      );
    }
    return null;
  };

  if (isLoading) {
    return <div>Loading risk assessment data...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold tracking-tight">Health Risk Analysis</h2>
          <p className="text-muted-foreground">
            Visualize and understand your health risk factors
          </p>
        </div>
        <div className="flex space-x-2">
          <Select value={selectedMetric} onValueChange={setSelectedMetric}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select metric" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="risk">Risk Score</SelectItem>
              <SelectItem value="severity">Severity</SelectItem>
              <SelectItem value="correlation">Correlation</SelectItem>
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

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Overall Risk Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={formatRiskData(riskAssessment)}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="name" />
                  <PolarRadiusAxis angle={30} domain={[0, 10]} />
                  <Radar
                    name="Risk Level"
                    dataKey={selectedMetric}
                    stroke={getChartColor(riskAssessment?.total_risk || 0)}
                    fill={getChartColor(riskAssessment?.total_risk || 0)}
                    fillOpacity={0.6}
                  />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Factors Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={formatRiskData(riskAssessment)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 10]} />
                  <Tooltip />
                  <Legend />
                  <Bar
                    dataKey="severity"
                    name="Severity"
                    fill="#ef4444"
                    opacity={0.8}
                  />
                  <Bar
                    dataKey="correlation"
                    name="Correlation"
                    fill="#3b82f6"
                    opacity={0.8}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Trend Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={formatRiskData(riskAssessment)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 10]} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="risk"
                    name="Risk Score"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {riskAssessment && renderSeverityAlert(riskAssessment.total_risk)}

      {riskAssessment?.recommendations && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {riskAssessment.recommendations}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
