provider "aws" {
  region = "eu-west-1"

  default_tags {
    tags = {
      Name        = "calendar"
      Project     = "opsmaster"
      Environment = "dev"
    }
  }
}

provider "aws" {
  alias  = "virginia"
  region = "us-east-1"

  default_tags {
    tags = {
      Name        = "calendar"
      Project     = "opsmaster"
      Environment = "dev"
    }
  }
}
