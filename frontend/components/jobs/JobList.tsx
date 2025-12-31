"use client";

import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { RefreshCw, Download } from "lucide-react";

interface Job {
  id: number;
  company: string;
  title: string;
  status?: string;
  match?: {
    fit_score: number;
    matching_skills?: string[];
    missing_skills?: string[];
  };
  date_added?: string;
  date_applied?: string;
  has_resume?: boolean;
  latest_resume_id?: number;
}

interface JobListProps {
  jobs: Job[];
  loading?: boolean;
  onRefresh?: () => void;
  onJobClick?: (job: Job) => void;
  statusFilter?: string;
  onStatusFilterChange?: (status: string) => void;
}

export function JobList({ 
  jobs, 
  loading, 
  onRefresh, 
  onJobClick,
  statusFilter = "all",
  onStatusFilterChange,
}: JobListProps) {
  const [sortConfig, setSortConfig] = useState<{
    key: keyof Job;
    direction: "asc" | "desc";
  } | null>(null);

  const statusOptions = ['all', 'New', 'Interested', 'Applied', 'Interview', 'Offer', 'Rejected', 'Withdrawn'];

  const handleSort = (key: keyof Job) => {
    let direction: "asc" | "desc" = "asc";
    if (
      sortConfig &&
      sortConfig.key === key &&
      sortConfig.direction === "asc"
    ) {
      direction = "desc";
    }
    setSortConfig({ key, direction });
  };

  // Filter jobs by status
  const filteredJobs = statusFilter === "all" 
    ? jobs 
    : jobs.filter(job => (job.status || "New") === statusFilter);

  const sortedJobs = [...filteredJobs].sort((a, b) => {
    if (!sortConfig) return 0;

    const aValue = a[sortConfig.key];
    const bValue = b[sortConfig.key];

    if (aValue === undefined || aValue === null) return 1;
    if (bValue === undefined || bValue === null) return -1;

    if (sortConfig.key === "match") {
      const aScore = a.match?.fit_score ?? 0;
      const bScore = b.match?.fit_score ?? 0;
      return sortConfig.direction === "asc"
        ? aScore - bScore
        : bScore - aScore;
    }

    if (typeof aValue === "string" && typeof bValue === "string") {
      return sortConfig.direction === "asc"
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    }

    return 0;
  });

  const getStatusColor = (status?: string) => {
    switch (status) {
      case "Applied":
        return "default";
      case "Interview":
        return "default";
      case "Offer":
        return "default";
      case "Rejected":
        return "destructive";
      case "Withdrawn":
        return "secondary";
      default:
        return "outline";
    }
  };

  const getRowClassName = (status?: string) => {
    const baseClass = "cursor-pointer hover:bg-gray-50";
    switch (status) {
      case "Rejected":
      case "Withdrawn":
        return `${baseClass} bg-red-50`;
      case "Offer":
        return `${baseClass} bg-green-50`;
      case "Applied":
      case "Interview":
        return `${baseClass} bg-yellow-50`;
      default:
        return baseClass;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Jobs</h2>
        <div className="flex items-center gap-2">
          <Select value={statusFilter} onValueChange={onStatusFilterChange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              {statusOptions.map((status) => (
                <SelectItem key={status} value={status}>
                  {status === "all" ? "All Statuses" : status}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {loading && jobs.length === 0 ? (
        <div className="text-center py-12" role="status" aria-live="polite">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" role="status">
            <span className="sr-only">Loading jobs...</span>
          </div>
          <p className="mt-4 text-muted-foreground">Loading jobs...</p>
        </div>
      ) : sortedJobs.length === 0 ? (
        <div className="text-center py-12 border rounded-lg bg-muted/30" role="status">
          <p className="text-lg font-medium mb-2">No jobs found</p>
          <p className="text-sm text-muted-foreground mb-4">
            {statusFilter === "all"
              ? "Get started by adding your first job application."
              : `No jobs with status "${statusFilter}". Try a different filter.`}
          </p>
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden w-full">
          <div className="job-table-container w-full">
            <Table className="w-full">
            <TableHeader>
              <TableRow>
                <TableHead>
                  <button
                    onClick={() => handleSort("company")}
                    className="flex items-center gap-1 hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded px-1"
                    aria-label={`Sort by company ${sortConfig?.key === "company" && sortConfig.direction === "asc" ? "descending" : "ascending"}`}
                  >
                    Company
                    {sortConfig?.key === "company" && (
                      <span className="text-xs" aria-hidden="true">
                        {sortConfig.direction === "asc" ? "↑" : "↓"}
                      </span>
                    )}
                  </button>
                </TableHead>
                <TableHead>
                  <button
                    onClick={() => handleSort("title")}
                    className="flex items-center gap-1 hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded px-1"
                    aria-label={`Sort by title ${sortConfig?.key === "title" && sortConfig.direction === "asc" ? "descending" : "ascending"}`}
                  >
                    Title
                    {sortConfig?.key === "title" && (
                      <span className="text-xs" aria-hidden="true">
                        {sortConfig.direction === "asc" ? "↑" : "↓"}
                      </span>
                    )}
                  </button>
                </TableHead>
                <TableHead>
                  <button
                    onClick={() => handleSort("status")}
                    className="flex items-center gap-1 hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded px-1"
                    aria-label={`Sort by status ${sortConfig?.key === "status" && sortConfig.direction === "asc" ? "descending" : "ascending"}`}
                  >
                    Status
                    {sortConfig?.key === "status" && (
                      <span className="text-xs" aria-hidden="true">
                        {sortConfig.direction === "asc" ? "↑" : "↓"}
                      </span>
                    )}
                  </button>
                </TableHead>
                <TableHead>
                  <button
                    onClick={() => handleSort("match")}
                    className="flex items-center gap-1 hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded px-1"
                    aria-label={`Sort by fit score ${sortConfig?.key === "match" && sortConfig.direction === "asc" ? "descending" : "ascending"}`}
                  >
                    Fit Score
                    {sortConfig?.key === "match" && (
                      <span className="text-xs" aria-hidden="true">
                        {sortConfig.direction === "asc" ? "↑" : "↓"}
                      </span>
                    )}
                  </button>
                </TableHead>
                <TableHead>
                  <button
                    onClick={() => handleSort("date_added")}
                    className="flex items-center gap-1 hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded px-1"
                    aria-label={`Sort by date added ${sortConfig?.key === "date_added" && sortConfig.direction === "asc" ? "descending" : "ascending"}`}
                  >
                    Date Added
                    {sortConfig?.key === "date_added" && (
                      <span className="text-xs" aria-hidden="true">
                        {sortConfig.direction === "asc" ? "↑" : "↓"}
                      </span>
                    )}
                  </button>
                </TableHead>
                <TableHead>
                  <button
                    onClick={() => handleSort("date_applied")}
                    className="flex items-center gap-1 hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded px-1"
                    aria-label={`Sort by date applied ${sortConfig?.key === "date_applied" && sortConfig.direction === "asc" ? "descending" : "ascending"}`}
                  >
                    Date Applied
                    {sortConfig?.key === "date_applied" && (
                      <span className="text-xs" aria-hidden="true">
                        {sortConfig.direction === "asc" ? "↑" : "↓"}
                      </span>
                    )}
                  </button>
                </TableHead>
                <TableHead>
                  <span className="sr-only">Actions</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedJobs.map((job) => (
                <TableRow
                  key={job.id}
                  className={`${getRowClassName(job.status)} focus-within:ring-2 focus-within:ring-ring`}
                  onClick={() => onJobClick?.(job)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onJobClick?.(job);
                    }
                  }}
                  tabIndex={0}
                  role="button"
                  aria-label={`View details for ${job.company} - ${job.title}`}
                >
                  <TableCell className="font-medium min-w-[100px]">{job.company}</TableCell>
                  <TableCell className="min-w-[120px]">{job.title}</TableCell>
                  <TableCell className="min-w-[90px]">
                    <Badge variant={getStatusColor(job.status)}>
                      {job.status || "New"}
                    </Badge>
                  </TableCell>
                  <TableCell className="min-w-[140px]">
                    {job.match?.fit_score !== undefined ? (
                      <div className="flex items-center gap-2">
                        <Progress 
                          value={job.match.fit_score * 100} 
                          className="flex-1 min-w-[60px]"
                        />
                        <span className="text-sm font-medium whitespace-nowrap">
                          {(job.match.fit_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    ) : (
                      "N/A"
                    )}
                  </TableCell>
                  <TableCell className="min-w-[100px] whitespace-nowrap">
                    {job.date_added
                      ? new Date(job.date_added).toLocaleDateString()
                      : "N/A"}
                  </TableCell>
                  <TableCell className="min-w-[100px] whitespace-nowrap">
                    {job.date_applied
                      ? new Date(job.date_applied).toLocaleDateString()
                      : "N/A"}
                  </TableCell>
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    {job.has_resume && job.latest_resume_id ? (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={async (e) => {
                          e.stopPropagation();
                          try {
                            const response = await fetch(
                              `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/resumes/${job.latest_resume_id}/render-pdf`,
                              { method: 'POST' }
                            );
                            const blob = await response.blob();
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement("a");
                            a.href = url;
                            a.download = `resume_${job.company}_${job.title}.pdf`;
                            document.body.appendChild(a);
                            a.click();
                            window.URL.revokeObjectURL(url);
                            document.body.removeChild(a);
                          } catch (err) {
                            // Silently handle download errors - user can retry
                          }
                        }}
                        aria-label="Download resume"
                        title="Download resume PDF"
                      >
                        <Download className="h-4 w-4" aria-hidden="true" />
                        <span className="sr-only">Download resume</span>
                      </Button>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          </div>
        </div>
      )}
    </div>
  );
}
