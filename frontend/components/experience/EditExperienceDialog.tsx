"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ExperienceForm } from "./ExperienceForm";
import { experienceApi } from "@/lib/api";

interface EditExperienceDialogProps {
  experience: any;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function EditExperienceDialog({
  experience,
  open,
  onOpenChange,
  onSuccess,
}: EditExperienceDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: {
    organization: string;
    role: string;
    location?: string;
    start_date?: string;
    end_date?: string;
    bullets: Array<{ text: string; skills?: string[]; evidence?: string }>;
  }) => {
    setLoading(true);
    setError(null);

    try {
      await experienceApi.update(
        experience.organization,
        experience.role,
        data
      );
      onOpenChange(false);
      onSuccess?.();
    } catch (err: any) {
      setError(err.message || "Failed to update experience");
    } finally {
      setLoading(false);
    }
  };

  if (!experience) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Experience</DialogTitle>
          <DialogDescription>
            Update experience information and bullets.
          </DialogDescription>
        </DialogHeader>

        <ExperienceForm
          initialValues={{
            organization: experience.organization,
            role: experience.role,
            location: experience.location,
            start_date: experience.start_date,
            end_date: experience.end_date,
            bullets: experience.bullets,
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
