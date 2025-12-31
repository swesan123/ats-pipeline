"use client";

import { useEffect, useState } from "react";
import { experienceApi } from "@/lib/api";
import { ExperienceList } from "@/components/experience/ExperienceList";
import { AddExperienceDialog } from "@/components/experience/AddExperienceDialog";
import { EditExperienceDialog } from "@/components/experience/EditExperienceDialog";
import {
  Alert,
  AlertDescription,
} from "@/components/ui/alert";

export default function ExperiencePage() {
  const [experiences, setExperiences] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedExperience, setSelectedExperience] = useState<any | null>(null);
  const [editOpen, setEditOpen] = useState(false);

  useEffect(() => {
    loadExperiences();
  }, []);

  const loadExperiences = async () => {
    try {
      setLoading(true);
      const data = await experienceApi.list();
      setExperiences(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load experiences");
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (experience: any) => {
    setSelectedExperience(experience);
    setEditOpen(true);
  };

  const handleDelete = async (organization: string, role: string) => {
    if (!confirm(`Are you sure you want to delete this experience entry?`)) {
      return;
    }

    try {
      await experienceApi.delete(organization, role);
      loadExperiences();
    } catch (err: any) {
      setError(err.message || "Failed to delete experience");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Experience</h1>
        <AddExperienceDialog onSuccess={loadExperiences} />
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>
            {error}
            <button
              onClick={loadExperiences}
              className="ml-2 underline hover:no-underline"
            >
              Retry
            </button>
          </AlertDescription>
        </Alert>
      )}

      {loading && experiences.length === 0 ? (
        <div className="text-center py-8 text-gray-500">Loading experiences...</div>
      ) : (
        <ExperienceList
          experiences={experiences}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}

      {selectedExperience && (
        <EditExperienceDialog
          experience={selectedExperience}
          open={editOpen}
          onOpenChange={setEditOpen}
          onSuccess={() => {
            loadExperiences();
            setSelectedExperience(null);
          }}
        />
      )}
    </div>
  );
}
