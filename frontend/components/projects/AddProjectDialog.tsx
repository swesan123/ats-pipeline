"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ProjectForm } from "./ProjectForm";
import { Loader2 } from "lucide-react";
import { projectsApi } from "@/lib/api";

interface AddProjectDialogProps {
  onSuccess?: () => void;
}

export function AddProjectDialog({ onSuccess }: AddProjectDialogProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("manual");
  const [githubUrl, setGithubUrl] = useState("");
  const [githubPreview, setGithubPreview] = useState<any | null>(null);
  const [githubLoading, setGithubLoading] = useState(false);

  const handleManualSubmit = async (data: {
    name: string;
    tech_stack: string[];
    start_date?: string;
    end_date?: string;
    bullets: Array<{ text: string; skills?: string[]; evidence?: string }>;
  }) => {
    setLoading(true);
    setError(null);

    try {
      await projectsApi.create(data);
      setOpen(false);
      onSuccess?.();
    } catch (err: any) {
      setError(err.message || "Failed to create project");
    } finally {
      setLoading(false);
    }
  };

  const handleGithubImport = async () => {
    if (!githubUrl) {
      setError("Please enter a GitHub repository URL");
      return;
    }

    setGithubLoading(true);
    setError(null);

    try {
      const project = await projectsApi.importFromGitHub(githubUrl);
      setGithubPreview(project);
    } catch (err: any) {
      setError(err.message || "Failed to import from GitHub");
    } finally {
      setGithubLoading(false);
    }
  };

  const handleGithubSave = async (data: {
    name: string;
    tech_stack: string[];
    start_date?: string;
    end_date?: string;
    bullets: Array<{ text: string; skills?: string[]; evidence?: string }>;
  }) => {
    setLoading(true);
    setError(null);

    try {
      await projectsApi.create(data);
      setOpen(false);
      setGithubPreview(null);
      setGithubUrl("");
      onSuccess?.();
    } catch (err: any) {
      setError(err.message || "Failed to save project");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Add Project</Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add New Project</DialogTitle>
          <DialogDescription>
            Add a project manually or import from GitHub.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="manual">Manual Entry</TabsTrigger>
            <TabsTrigger value="github">GitHub Import</TabsTrigger>
          </TabsList>

          <TabsContent value="manual" className="space-y-4">
            <ProjectForm
              onSubmit={handleManualSubmit}
              onCancel={() => setOpen(false)}
              loading={loading}
            />
          </TabsContent>

          <TabsContent value="github" className="space-y-4">
            {!githubPreview ? (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">GitHub Repository URL</label>
                  <Input
                    placeholder="https://github.com/owner/repo"
                    value={githubUrl}
                    onChange={(e) => setGithubUrl(e.target.value)}
                  />
                  <p className="text-xs text-gray-500">
                    Enter the full URL of the GitHub repository
                  </p>
                </div>

                <Button
                  onClick={handleGithubImport}
                  disabled={githubLoading || !githubUrl}
                  className="w-full"
                >
                  {githubLoading && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Import from GitHub
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-semibold mb-2">Preview Extracted Project</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Review and edit the extracted information before saving.
                  </p>
                </div>

                <ProjectForm
                  initialValues={{
                    name: githubPreview.name,
                    tech_stack: githubPreview.tech_stack,
                    start_date: githubPreview.start_date,
                    end_date: githubPreview.end_date,
                    bullets: githubPreview.bullets,
                  }}
                  onSubmit={handleGithubSave}
                  onCancel={() => {
                    setGithubPreview(null);
                    setGithubUrl("");
                  }}
                  loading={loading}
                />
              </div>
            )}
          </TabsContent>
        </Tabs>

        {error && (
          <div className="text-sm text-red-500 bg-red-50 p-3 rounded">
            {error}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
