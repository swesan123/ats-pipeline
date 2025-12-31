"use client";

import { useEffect, useState } from "react";
import { projectsApi } from "@/lib/api";
import { ProjectList } from "@/components/projects/ProjectList";
import { AddProjectDialog } from "@/components/projects/AddProjectDialog";
import { EditProjectDialog } from "@/components/projects/EditProjectDialog";
import {
  Alert,
  AlertDescription,
} from "@/components/ui/alert";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<any | null>(null);
  const [editOpen, setEditOpen] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await projectsApi.list();
      setProjects(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (project: any) => {
    setSelectedProject(project);
    setEditOpen(true);
  };

  const handleDelete = async (projectName: string) => {
    if (!confirm(`Are you sure you want to delete "${projectName}"?`)) {
      return;
    }

    try {
      await projectsApi.delete(projectName);
      loadProjects();
    } catch (err: any) {
      setError(err.message || "Failed to delete project");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Projects</h1>
        <AddProjectDialog onSuccess={loadProjects} />
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>
            {error}
            <button
              onClick={loadProjects}
              className="ml-2 underline hover:no-underline"
            >
              Retry
            </button>
          </AlertDescription>
        </Alert>
      )}

      {loading && projects.length === 0 ? (
        <div className="text-center py-8 text-gray-500">Loading projects...</div>
      ) : (
        <ProjectList
          projects={projects}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}

      {selectedProject && (
        <EditProjectDialog
          project={selectedProject}
          open={editOpen}
          onOpenChange={setEditOpen}
          onSuccess={() => {
            loadProjects();
            setSelectedProject(null);
          }}
        />
      )}
    </div>
  );
}
