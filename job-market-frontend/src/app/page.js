"use client";
import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { toPng } from 'html-to-image';
import { PDFDocument, rgb } from 'pdf-lib';

export default function JobMarketAnalysis() {
  const [formData, setFormData] = useState({
    country: "India",
    city: "Bangalore",
    job_role: "Software Engineer",
    include_skills: true,
    include_salaries: true,
    include_companies: true,
    include_trends: true,
  });

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [progress, setProgress] = useState([]);
  const [report, setReport] = useState("");
  const [error, setError] = useState("");
  const [currentAgent, setCurrentAgent] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const activityLogRef = useRef(null);
  const reportRef = useRef(null);

  const eventSourceRef = useRef(null);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const extractChartData = (reportText) => {
    const pattern = /(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s*\n(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)/;
    const match = reportText.match(pattern);
    
    if (match) {
      const months = match.slice(1, 8);
      const values = match.slice(8, 15).map(Number);
      
      const data = months.map((month, index) => ({
        name: month,
        value: values[index]
      }));
      
      setChartData(data);
    }
  };

  const startAnalysis = async () => {
    setIsAnalyzing(true);
    setProgress([]);
    setReport("");
    setError("");
    setCurrentAgent(null);
    setChartData(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/analysis/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await response.json();
      setTaskId(data.task_id);
      connectToSSE(data.task_id);
    } catch (err) {
      setError("Failed to start analysis. Please try again.");
      setIsAnalyzing(false);
    }
  };

  const connectToSSE = (taskId) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(
      `http://127.0.0.1:8000/events/stream/${taskId}`
    );
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case "CREW_STARTED":
            setProgress((prev) => [
              ...prev,
              {
                type: "info",
                message: `Analysis started for ${data.data.job_role} in ${data.data.city}, ${data.data.country}`,
              },
            ]);
            break;

          case "AGENT_ACTION":
            setProgress((prev) => [
              ...prev,
              {
                type: "action",
                agent: data.data.agent,
                task: data.data.task,
                step: data.data.step,
              },
            ]);
            setCurrentAgent(data.data.agent);
            break;
          
          case "TASK_STATUS":
            setProgress((prev) => [
              ...prev,
              {
                type: "task",
                task: data.data.task,
                status: data.data.status,
              },
            ]);
            break;  

          case "CREW_COMPLETED":
            const cleanedResult = data.data.result.startsWith("**") 
              ? data.data.result.substring(2) 
              : data.data.result;
            setReport(cleanedResult);
            extractChartData(cleanedResult);
            setProgress((prev) => [
              ...prev,
              {
                type: "success",
                message: "Analysis completed successfully!",
              },
            ]);
            setIsAnalyzing(false);
            eventSource.close();
            break;

          case "CREW_ERROR":
            setError(data.data.error);
            setProgress((prev) => [
              ...prev,
              {
                type: "error",
                message: `Error: ${data.data.error}`,
              },
            ]);
            setIsAnalyzing(false);
            eventSource.close();
            break;

          default:
            console.log("Unhandled event type:", data.type);
        }
      } catch (e) {
        console.error("Error parsing event data:", e);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE connection error:", err);
      setError("Connection lost. Reconnecting...");
      setTimeout(() => connectToSSE(taskId), 3000);
    };
  };

  const generatePDF = async () => {
    if (!reportRef.current) return;
  
    setIsGeneratingPDF(true);
    try {
      // Create image from HTML with proper dimensions
      const dataUrl = await toPng(reportRef.current, {
        quality: 1,
        pixelRatio: 2,
        backgroundColor: '#ffffff',
        width: 800, // Fixed width
        height: reportRef.current.scrollHeight, // Dynamic height
        style: {
          wordWrap: 'break-word',
          overflowWrap: 'break-word',
          whiteSpace: 'pre-wrap'
        }
      });
  
      // Create PDF with proper margins
      const pdfDoc = await PDFDocument.create();
      const page = pdfDoc.addPage([595, 842]); // A4 size in points
  
      // Embed the image
      const imageBytes = await fetch(dataUrl).then(res => res.arrayBuffer());
      const image = await pdfDoc.embedPng(imageBytes);
      
      // Scale image to fit page width with margins
      const scale = (page.getWidth() - 100) / image.width;
      page.drawImage(image, {
        x: 50,
        y: page.getHeight() - (image.height * scale) - 50,
        width: image.width * scale,
        height: image.height * scale,
      });
  
      // Add title with proper wrapping
      const title = `Job Market Analysis - ${formData.job_role} in ${formData.city}, ${formData.country}`;
      const fontSize = 14;
      const textWidth = 500; // Max width for text
      page.drawText(title, {
        x: 50,
        y: page.getHeight() - 30,
        size: fontSize,
        maxWidth: textWidth,
        lineHeight: fontSize * 1.2,
        color: rgb(0, 0, 0),
      });
  
      // Save the PDF
      const pdfBytes = await pdfDoc.save();
  
      // Download the PDF
      const blob = new Blob([pdfBytes], { type: 'application/pdf' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `job-market-analysis-${new Date().toISOString().slice(0, 10)}.pdf`;
      link.click();
    } catch (error) {
      console.error('Error generating PDF:', error);
      setError('Failed to generate PDF. Please try again.');
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  useEffect(() => {
    if (activityLogRef.current) {
      activityLogRef.current.scrollTop = activityLogRef.current.scrollHeight;
    }
  }, [progress]);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const components = {
    table: ({ node, ...props }) => (
      <div className="overflow-x-auto">
        <table className="min-w-full border border-gray-200" {...props} />
      </div>
    ),
    th: ({ node, ...props }) => (
      <th className="border border-gray-200 px-4 py-2 bg-gray-50 font-medium" {...props} />
    ),
    td: ({ node, ...props }) => (
      <td className="border border-gray-200 px-4 py-2" {...props} />
    ),
    a: ({ node, ...props }) => (
      <a className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />
    ),
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
                LaborLens AI
              </h1>
              <p className="text-gray-600 max-w-2xl">
                Advanced Job Market Intelligence Platform
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isAnalyzing ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
              <span className="text-sm text-gray-500">
                {isAnalyzing ? 'Live Analysis' : 'Ready'}
              </span>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 gap-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <Card className="h-full">
                <CardHeader>
                  <CardTitle>Analysis Parameters</CardTitle>
                  <CardDescription>
                    Configure your job market analysis
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="country">Country</Label>
                      <Input
                        id="country"
                        name="country"
                        value={formData.country}
                        onChange={handleChange}
                        disabled={isAnalyzing}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="city">City</Label>
                      <Input
                        id="city"
                        name="city"
                        value={formData.city}
                        onChange={handleChange}
                        disabled={isAnalyzing}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="job_role">Job Role</Label>
                      <Input
                        id="job_role"
                        name="job_role"
                        value={formData.job_role}
                        onChange={handleChange}
                        disabled={isAnalyzing}
                      />
                    </div>

                    <div className="space-y-4">
                      <Label>Include in Report</Label>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="include_skills"
                            name="include_skills"
                            checked={formData.include_skills}
                            onCheckedChange={(checked) =>
                              setFormData((prev) => ({
                                ...prev,
                                include_skills: checked,
                              }))
                            }
                            disabled={isAnalyzing}
                          />
                          <Label htmlFor="include_skills">Skills</Label>
                        </div>

                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="include_salaries"
                            name="include_salaries"
                            checked={formData.include_salaries}
                            onCheckedChange={(checked) =>
                              setFormData((prev) => ({
                                ...prev,
                                include_salaries: checked,
                              }))
                            }
                            disabled={isAnalyzing}
                          />
                          <Label htmlFor="include_salaries">Salaries</Label>
                        </div>

                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="include_companies"
                            name="include_companies"
                            checked={formData.include_companies}
                            onCheckedChange={(checked) =>
                              setFormData((prev) => ({
                                ...prev,
                                include_companies: checked,
                              }))
                            }
                            disabled={isAnalyzing}
                          />
                          <Label htmlFor="include_companies">Companies</Label>
                        </div>

                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="include_trends"
                            name="include_trends"
                            checked={formData.include_trends}
                            onCheckedChange={(checked) =>
                              setFormData((prev) => ({
                                ...prev,
                                include_trends: checked,
                              }))
                            }
                            disabled={isAnalyzing}
                          />
                          <Label htmlFor="include_trends">Market Trends</Label>
                        </div>
                      </div>
                    </div>

                    <Button
                      onClick={startAnalysis}
                      disabled={isAnalyzing}
                      className="w-full"
                    >
                      {isAnalyzing ? (
                        <>
                          <svg
                            className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                          >
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                            ></circle>
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            ></path>
                          </svg>
                          Analyzing...
                        </>
                      ) : (
                        "Start Analysis"
                      )}
                    </Button>

                    {error && (
                      <div className="p-3 bg-red-50 text-red-700 rounded-md">
                        {error}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            <div>
              <Card className="h-full">
                <CardHeader>
                  <CardTitle>Analysis Progress</CardTitle>
                  <CardDescription>
                    {isAnalyzing
                      ? "Real-time task tracking"
                      : "Analysis not started"}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {isAnalyzing ? (
                    <div className="space-y-6">
                      <div className="space-y-4">
                        <h3 className="font-medium">Current Agent</h3>
                        {currentAgent && (
                          <Badge variant="secondary" className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-green-500"></div>
                            {currentAgent}
                          </Badge>
                        )}
                      </div>

                      <div className="space-y-4">
                        <h3 className="font-medium">Activity Log</h3>
                        <div 
                          ref={activityLogRef}
                          className="h-64 overflow-y-auto border rounded-lg p-4 bg-gray-50"
                        >
                          {progress.map((item, index) => (
                            <div
                              key={index}
                              className={`py-2 px-3 mb-2 rounded-md text-sm ${
                                item.type === "error"
                                  ? "bg-red-50 text-red-700"
                                  : item.type === "success"
                                  ? "bg-green-50 text-green-700"
                                  : item.type === "task"
                                  ? "bg-blue-50 text-blue-700"
                                  : "bg-gray-50 text-gray-700"
                              }`}
                            >
                              {item.type === "action" && (
                                <div className="flex items-start">
                                  <div className="mr-2 mt-1">
                                    <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                                  </div>
                                  <div>
                                    <span className="font-medium">
                                      {item.agent}
                                    </span>{" "}
                                    is working on: {item.task}
                                    <div className="text-xs mt-1 opacity-80">
                                      {typeof item.step === "string" 
                                        ? item.step 
                                        : JSON.stringify(item.step)}
                                    </div>
                                  </div>
                                </div>
                              )}

                              {["info", "success", "error"].includes(item.type) && (
                                <div className="flex items-start">
                                  <div className="mr-2 mt-1">
                                    <div className={`w-2 h-2 rounded-full ${
                                      item.type === "error" ? "bg-red-500" :
                                      item.type === "success" ? "bg-green-500" :
                                      "bg-gray-500"
                                    }`}></div>
                                  </div>
                                  <div>{item.message}</div>
                                </div>
                              )}
                            </div>
                          ))}

                          {progress.length === 0 && (
                            <div className="text-center text-gray-500 py-8">
                              Waiting for analysis to begin...
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-64 text-center">
                      <h3 className="text-lg font-medium mb-1">
                        No active analysis
                      </h3>
                      <p className="text-gray-500 text-sm">
                        Start an analysis to see real-time progress and agent
                        activity
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>

          <div>
            <Card className="h-full">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Analysis Report</CardTitle>
                    <CardDescription>
                      {report
                        ? "Comprehensive job market insights"
                        : "Report will appear here"}
                    </CardDescription>
                  </div>
                  {report && (
                    <Button 
                      variant="outline" 
                      onClick={generatePDF}
                      disabled={isGeneratingPDF}
                      className="ml-4"
                    >
                      {isGeneratingPDF ? 'Generating PDF...' : 'Download PDF'}
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="h-full">
              <div ref={reportRef} className="space-y-6" style={{
                width: '100%',
                maxWidth: '800px', // Constrain width for better PDF rendering
                wordWrap: 'break-word',
                overflowWrap: 'break-word',
                whiteSpace: 'pre-wrap'
              }}>
                  {report ? (
                    <div className="space-y-6">
                      <div className="prose max-w-none">
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm]} 
                          components={components}
                        >
                          {report}
                        </ReactMarkdown>
                      </div>
                      
                      {chartData && (
                        <div className="mt-8">
                          <h3 className="text-lg font-medium mb-4">Job Growth Visualization</h3>
                          <div className="h-80">
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart
                                data={chartData}
                                margin={{
                                  top: 5,
                                  right: 30,
                                  left: 20,
                                  bottom: 5,
                                }}
                              >
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="name" />
                                <YAxis />
                                <Tooltip />
                                <Bar dataKey="value" fill="#8884d8" />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : isAnalyzing ? (
                    <div className="space-y-4">
                      <div className="space-y-3">
                        <Skeleton className="h-4 w-full rounded" />
                        <Skeleton className="h-4 w-5/6 rounded" />
                        <Skeleton className="h-4 w-4/6 rounded" />
                      </div>
                      <div className="space-y-3 pt-4">
                        <Skeleton className="h-4 w-full rounded" />
                        <Skeleton className="h-4 w-full rounded" />
                        <Skeleton className="h-4 w-full rounded" />
                        <Skeleton className="h-4 w-3/4 rounded" />
                      </div>
                      <div className="space-y-3 pt-4">
                        <Skeleton className="h-4 w-full rounded" />
                        <Skeleton className="h-4 w-5/6 rounded" />
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-64 text-center">
                      <h3 className="text-lg font-medium mb-1">
                        No report generated
                      </h3>
                      <p className="text-gray-500 text-sm">
                        Complete an analysis to generate a detailed market report
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <footer className="mt-12 text-center text-gray-500 text-sm">
          <p>© {new Date().getFullYear()} LaborLens • Real-time Market Intelligence</p>
        </footer>
      </div>
    </div>
  );
}