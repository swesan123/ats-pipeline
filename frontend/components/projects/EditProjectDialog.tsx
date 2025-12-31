"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ProjectForm } from "./ProjectForm";
import { projectsApi } from "@/lib/api";

interface EditProjectDialogProps {
  project: any;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function EditProjectDialog({
  project,
  open,
  onOpenChange,
  onSuccess,
}: EditProjectDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: {
    name: string;
    tech_stack: string[];
    start_date?: string;
    end_date?: string;
    bullets: Array<{ text: string; skills?: string[]; evidence?: string }>;
  }) => {
    setLoading(true);
    setError(null);

    try {
      await projectsApi.update(project.name, data);
      onOpenChange(false);
      onSuccess?.();
    } catch (err: any) {
      setError(err.message || "Failed to update project");
    } finally {
      setLoading(false);
    }
  };

  if (!project) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Project</DialogTitle>
          <DialogDescription>
            Update project information and bullets.
          </DialogDescription>
        </DialogHeader>

        <ProjectForm
          initialValues={{
            name: project.name,
            tech_stack: project.tech_stack,
            start_date: project.start_date,
            end_date: project.end_date,
            bullets: project.bullets,
          }}
          onSubmit={handleSubmit}
          onCancel={() => onOpenChange(false)}
          loading={loading}
        />

        {error && (
          <div className="text-sm text-red-500 bg-red-50 p-3 rounded">
            {error}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
