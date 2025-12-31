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
import { ExperienceForm } from "./ExperienceForm";
import { experienceApi } from "@/lib/api";

interface AddExperienceDialogProps {
  onSuccess?: () => void;
}

export function AddExperienceDialog({ onSuccess }: AddExperienceDialogProps) {
  const [open, setOpen] = useState(false);
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
      await experienceApi.create(data);
      setOpen(false);
      onSuccess?.();
    } catch (err: any) {
      setError(err.message || "Failed to create experience");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Add Experience</Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add New Experience</DialogTitle>
          <DialogDescription>
            Add a work experience entry with bullets.
          </DialogDescription>
        </DialogHeader>

        <ExperienceForm
          onSubmit={handleSubmit}
          onCancel={() => setOpen(false)}
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
