"use client";

import { useEffect, useState } from "react";
import { jobsApi } from "@/lib/api";
import { JobList } from "@/components/jobs/JobList";
import { AddJobDialog } from "@/components/jobs/AddJobDialog";
import { JobDetailsPanel } from "@/components/jobs/JobDetailsPanel";
import { GoogleSheetsSync } from "@/components/jobs/GoogleSheetsSync";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ChevronDown, RefreshCw, AlertCircle } from "lucide-react";

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<any | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [sheetsSyncOpen, setSheetsSyncOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await jobsApi.list(statusFilter === "all" ? undefined : statusFilter);
      setJobs(data);
    } catch (err: any) {
      setError(err.message || "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, [statusFilter]);

  const handleJobClick = (job: any) => {
    setSelectedJob(job);
    setDetailsOpen(true);
  };

  const handleJobUpdate = () => {
    loadJobs();
  };

  const handleJobDelete = () => {
    loadJobs();
    setSelectedJob(null);
    setDetailsOpen(false);
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <header className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">Jobs</h1>
            <p className="text-muted-foreground mt-1">
              Manage your job applications and track your progress
            </p>
          </div>
          <AddJobDialog onSuccess={loadJobs} />
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" role="alert">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="flex items-center justify-between">
              <span>{error}</span>
              <Button
                variant="outline"
                size="sm"
                onClick={loadJobs}
                className="ml-4"
                aria-label="Retry loading jobs"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Google Sheets Sync Section */}
        <Collapsible open={sheetsSyncOpen} onOpenChange={setSheetsSyncOpen}>
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              className="w-full justify-between"
              aria-expanded={sheetsSyncOpen}
              aria-controls="sheets-sync-content"
            >
              <span>Google Sheets Sync</span>
              <ChevronDown
                className={`h-4 w-4 transition-transform duration-200 ${
                  sheetsSyncOpen ? "rotate-180" : ""
                }`}
                aria-hidden="true"
              />
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent id="sheets-sync-content" className="mt-2">
            <GoogleSheetsSync />
          </CollapsibleContent>
        </Collapsible>
      </header>

      {/* Job List */}
      <section aria-label="Job applications list">
        <JobList
          jobs={jobs}
          loading={loading}
          onRefresh={loadJobs}
          onJobClick={handleJobClick}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
        />
      </section>

      {/* Job Details Drawer */}
      {selectedJob && (
        <JobDetailsPanel
          job={selectedJob}
          open={detailsOpen}
          onOpenChange={setDetailsOpen}
          onUpdate={handleJobUpdate}
          onDelete={handleJobDelete}
        />
      )}
    </div>
  );
}
