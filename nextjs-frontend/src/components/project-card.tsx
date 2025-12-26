import {Project} from "../lib/types"
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"; // Assuming you use shadcn/ui
import { Button } from "@/components/ui/button";

// Helper function to format the date
function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export function ProjectCard({ project }: { project: Project }) {
  return (
    <Card className="flex flex-col h-full transition-all hover:shadow-lg">
      <CardHeader>
        <CardTitle className="text-xl font-bold">{project.name}</CardTitle>
        <CardDescription>
          Created by {project.owner.email}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-grow">
        <p className="text-muted-foreground">
          {project.description || "No description provided."}
        </p>
      </CardContent>
      <CardFooter className="flex justify-between items-center mt-4">
        <p className="text-sm text-muted-foreground">
          {formatDate(project.created_at)}
        </p>
        <Link href={`/dashboard/projects/${project.id}`}>
            <Button variant="outline" size="sm" className="cursor-pointer">View Project</Button>
        </Link>
      </CardFooter>
    </Card>
  );
}