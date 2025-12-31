"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Edit, Trash2 } from "lucide-react";

interface Project {
  name: string;
  tech_stack?: string[];
  start_date?: string;
  end_date?: string;
  bullets?: Array<{ text: string }>;
}

interface ProjectListProps {
  projects: Project[];
  onEdit?: (project: Project) => void;
  onDelete?: (projectName: string) => void;
}

export function ProjectList({
  projects,
  onEdit,
  onDelete,
}: ProjectListProps) {
  if (projects.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No projects added yet. Add a project to get started.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {projects.map((project) => (
        <Card key={project.name}>
          <CardHeader>
            <div className="flex items-start justify-between">
              <CardTitle className="text-lg">{project.name}</CardTitle>
              <div className="flex gap-2">
                {onEdit && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit(project)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                )}
                {onDelete && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(project.name)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
            {(project.start_date || project.end_date) && (
              <p className="text-sm text-gray-600">
                {project.start_date || "?"} - {project.end_date || "Present"}
              </p>
            )}
          </CardHeader>
          <CardContent className="space-y-3">
            {project.tech_stack && project.tech_stack.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-600 mb-2">
                  Tech Stack:
                </p>
                <div className="flex flex-wrap gap-1">
                  {project.tech_stack.map((tech) => (
                    <Badge key={tech} variant="outline">
                      {tech}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {project.bullets && project.bullets.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-600 mb-2">
                  Bullets ({project.bullets.length}):
                </p>
                <ul className="text-sm text-gray-700 space-y-1">
                  {project.bullets.slice(0, 3).map((bullet, idx) => (
                    <li key={idx} className="list-disc list-inside">
                      {bullet.text.length > 100
                        ? `${bullet.text.substring(0, 100)}...`
                        : bullet.text}
                    </li>
                  ))}
                  {project.bullets.length > 3 && (
                    <li className="text-xs text-gray-500">
                      +{project.bullets.length - 3} more
                    </li>
                  )}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
