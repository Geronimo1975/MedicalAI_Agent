import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { Upload, FileType, MoreVertical, Download, Archive } from "lucide-react";

interface Document {
  id: number;
  title: string;
  file_type: string;
  shared_by_id: number;
  shared_with_id: number;
  created_at: string;
  description: string;
  category: string;
  is_archived: boolean;
  shared_by_name: string;
  shared_with_name: string;
}

interface UploadFormData {
  file: File;
  title: string;
  description?: string;
  category?: string;
  shared_with_id: number;
}

export default function DocumentManager() {
  const [uploadProgress, setUploadProgress] = useState(0);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: documents, isLoading } = useQuery<Document[]>({
    queryKey: ['/api/documents'],
  });

  const uploadMutation = useMutation({
    mutationFn: async (formData: UploadFormData) => {
      const data = new FormData();
      data.append('file', formData.file);
      data.append('title', formData.title);
      if (formData.description) data.append('description', formData.description);
      if (formData.category) data.append('category', formData.category);
      data.append('shared_with_id', formData.shared_with_id.toString());

      const xhr = new XMLHttpRequest();

      return new Promise((resolve, reject) => {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = (event.loaded / event.total) * 100;
            setUploadProgress(progress);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.response));
          } else {
            reject(new Error(xhr.response));
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Upload failed'));
        });

        xhr.open('POST', '/api/documents');
        xhr.withCredentials = true;
        xhr.send(data);
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/documents'] });
      toast({
        title: "Upload successful",
        description: "Your document has been uploaded successfully.",
      });
      setUploadProgress(0);
    },
    onError: (error: Error) => {
      toast({
        title: "Upload failed",
        description: error.message,
        variant: "destructive",
      });
      setUploadProgress(0);
    },
  });

  const archiveMutation = useMutation({
    mutationFn: async (documentId: number) => {
      const response = await fetch(`/api/documents/${documentId}/archive`, {
        method: 'PUT',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to archive document');
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/documents'] });
      toast({
        title: "Status updated",
        description: "Document status has been updated.",
      });
    },
  });

  const handleDownload = async (documentId: number) => {
    try {
      window.open(`/api/documents/${documentId}/download`, '_blank');
    } catch (error) {
      toast({
        title: "Download failed",
        description: "Failed to download the document.",
        variant: "destructive",
      });
    }
  };

  const handleFileUpload = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const file = formData.get('file') as File;

    if (!file) {
      toast({
        title: "No file selected",
        description: "Please select a file to upload.",
        variant: "destructive",
      });
      return;
    }

    try {
      await uploadMutation.mutateAsync({
        file,
        title: formData.get('title') as string || file.name,
        description: formData.get('description') as string,
        category: formData.get('category') as string,
        shared_with_id: parseInt(formData.get('shared_with_id') as string),
      });
      form.reset();
    } catch (error) {
      console.error('Upload error:', error);
    }
  };

  return (
    <div className="space-y-4">
      <Dialog>
        <DialogTrigger asChild>
          <Button>
            <Upload className="h-4 w-4 mr-2" />
            Upload Document
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Upload Medical Document</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleFileUpload} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">File</label>
              <input
                type="file"
                name="file"
                accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
                className="w-full"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Title</label>
              <input
                type="text"
                name="title"
                className="w-full px-3 py-2 border rounded-md"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                name="description"
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Category</label>
              <select
                name="category"
                className="w-full px-3 py-2 border rounded-md"
                required
              >
                <option value="lab_result">Lab Result</option>
                <option value="prescription">Prescription</option>
                <option value="scan">Medical Scan</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Share with</label>
              <input
                type="number"
                name="shared_with_id"
                className="w-full px-3 py-2 border rounded-md"
                placeholder="Enter user ID"
                required
              />
            </div>
            {uploadProgress > 0 && (
              <Progress value={uploadProgress} className="w-full" />
            )}
            <Button type="submit" className="w-full">
              Upload
            </Button>
          </form>
        </DialogContent>
      </Dialog>

      {isLoading ? (
        <div>Loading documents...</div>
      ) : documents?.length ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className={`p-4 border rounded-lg ${
                doc.is_archived ? "opacity-50" : ""
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <FileType className="h-4 w-4 mr-2" />
                  <span className="font-medium">{doc.title}</span>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    <DropdownMenuItem onClick={() => handleDownload(doc.id)}>
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => archiveMutation.mutate(doc.id)}>
                      <Archive className="h-4 w-4 mr-2" />
                      {doc.is_archived ? "Unarchive" : "Archive"}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              <div className="text-sm text-gray-500 space-y-1">
                <p>Category: {doc.category}</p>
                <p>Shared by: {doc.shared_by_name}</p>
                <p>Shared with: {doc.shared_with_name}</p>
                <p>Date: {new Date(doc.created_at).toLocaleDateString()}</p>
                {doc.description && <p>Description: {doc.description}</p>}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-4">
          <p className="text-gray-500">No documents found</p>
        </div>
      )}
    </div>
  );
}