"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Edit, Trash2 } from "lucide-react";

interface Experience {
  organization: string;
  role: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  bullets?: Array<{ text: string }>;
}

interface ExperienceListProps {
  experiences: Experience[];
  onEdit?: (experience: Experience) => void;
  onDelete?: (organization: string, role: string) => void;
}

export function ExperienceList({
  experiences,
  onEdit,
  onDelete,
}: ExperienceListProps) {
  if (experiences.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No experience entries added yet. Add an experience to get started.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {experiences.map((exp, idx) => (
        <Card key={`${exp.organization}-${exp.role}-${idx}`}>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-lg">{exp.role}</CardTitle>
                <p className="text-sm text-gray-600">{exp.organization}</p>
                {exp.location && (
                  <p className="text-sm text-gray-500">{exp.location}</p>
                )}
                {(exp.start_date || exp.end_date) && (
                  <p className="text-sm text-gray-500 mt-1">
                    {exp.start_date || "?"} - {exp.end_date || "Present"}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                {onEdit && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit(exp)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                )}
                {onDelete && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(exp.organization, exp.role)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          {exp.bullets && exp.bullets.length > 0 && (
            <CardContent>
              <ul className="text-sm text-gray-700 space-y-1">
                {exp.bullets.map((bullet, bulletIdx) => (
                  <li key={bulletIdx} className="list-disc list-inside">
                    {bullet.text}
                  </li>
                ))}
              </ul>
            </CardContent>
          )}
        </Card>
      ))}
    </div>
  );
}
