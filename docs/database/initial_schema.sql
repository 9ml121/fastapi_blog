BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> b9cf7908383e

CREATE TABLE tags (
    id UUID NOT NULL, 
    name VARCHAR(50) NOT NULL, 
    slug VARCHAR(100) NOT NULL, 
    description TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

COMMENT ON COLUMN tags.id IS '标签唯一标识符';

COMMENT ON COLUMN tags.name IS '标签名称（唯一）';

COMMENT ON COLUMN tags.slug IS 'URL 友好的标识符';

COMMENT ON COLUMN tags.description IS '标签描述';

COMMENT ON COLUMN tags.created_at IS '创建时间';

COMMENT ON COLUMN tags.updated_at IS '更新时间';

CREATE UNIQUE INDEX ix_tags_name ON tags (name);

CREATE UNIQUE INDEX ix_tags_slug ON tags (slug);

CREATE TYPE userrole AS ENUM ('USER', 'ADMIN');

CREATE TABLE users (
    id UUID NOT NULL, 
    username VARCHAR(50) NOT NULL, 
    email VARCHAR(100) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    nickname VARCHAR(50) NOT NULL, 
    avatar VARCHAR(255), 
    role userrole NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    is_verified BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    last_login TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

COMMENT ON COLUMN users.id IS '用户唯一标识';

COMMENT ON COLUMN users.username IS '用户名（唯一）';

COMMENT ON COLUMN users.email IS '邮箱地址（唯一）';

COMMENT ON COLUMN users.password_hash IS '密码哈希值';

COMMENT ON COLUMN users.nickname IS '显示昵称';

COMMENT ON COLUMN users.avatar IS '头像文件路径';

COMMENT ON COLUMN users.role IS '用户角色';

COMMENT ON COLUMN users.is_active IS '账户是否激活（软删除标记）';

COMMENT ON COLUMN users.is_verified IS '邮箱是否已验证';

COMMENT ON COLUMN users.created_at IS '创建时间';

COMMENT ON COLUMN users.updated_at IS '更新时间';

COMMENT ON COLUMN users.last_login IS '最后登录时间';

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE UNIQUE INDEX ix_users_username ON users (username);

CREATE TYPE poststatus AS ENUM ('DRAFT', 'PUBLISHED', 'ARCHIVED');

CREATE TABLE posts (
    id UUID NOT NULL, 
    title VARCHAR(200) NOT NULL, 
    content TEXT NOT NULL, 
    summary VARCHAR(500), 
    slug VARCHAR(200) NOT NULL, 
    status poststatus NOT NULL, 
    is_featured BOOLEAN NOT NULL, 
    view_count INTEGER NOT NULL, 
    author_id UUID NOT NULL, 
    published_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(author_id) REFERENCES users (id) ON DELETE CASCADE
);

COMMENT ON COLUMN posts.id IS '文章唯一标识';

COMMENT ON COLUMN posts.title IS '文章标题';

COMMENT ON COLUMN posts.content IS '文章正文内容（Markdown 格式）';

COMMENT ON COLUMN posts.summary IS '文章摘要（用于列表页展示）';

COMMENT ON COLUMN posts.slug IS 'URL 友好标识（SEO 优化）';

COMMENT ON COLUMN posts.status IS '文章状态';

COMMENT ON COLUMN posts.is_featured IS '是否置顶文章';

COMMENT ON COLUMN posts.view_count IS '浏览次数统计';

COMMENT ON COLUMN posts.author_id IS '作者用户 ID';

COMMENT ON COLUMN posts.published_at IS '发布时间（仅发布后设置）';

COMMENT ON COLUMN posts.created_at IS '创建时间';

COMMENT ON COLUMN posts.updated_at IS '更新时间';

CREATE INDEX ix_posts_author_id ON posts (author_id);

CREATE INDEX ix_posts_created_at ON posts (created_at);

CREATE INDEX ix_posts_is_featured ON posts (is_featured);

CREATE INDEX ix_posts_published_at ON posts (published_at);

CREATE UNIQUE INDEX ix_posts_slug ON posts (slug);

CREATE INDEX ix_posts_status ON posts (status);

CREATE INDEX ix_posts_title ON posts (title);

CREATE TABLE comments (
    id UUID NOT NULL, 
    content TEXT NOT NULL, 
    user_id UUID NOT NULL, 
    post_id UUID NOT NULL, 
    parent_id UUID, 
    is_approved BOOLEAN NOT NULL, 
    is_deleted BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(parent_id) REFERENCES comments (id) ON DELETE CASCADE, 
    FOREIGN KEY(post_id) REFERENCES posts (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

COMMENT ON COLUMN comments.content IS '评论内容';

COMMENT ON COLUMN comments.user_id IS '评论作者 ID';

COMMENT ON COLUMN comments.post_id IS '所属文章 ID';

COMMENT ON COLUMN comments.parent_id IS '父评论 ID（顶级评论为 None）';

COMMENT ON COLUMN comments.is_approved IS '是否审核通过';

COMMENT ON COLUMN comments.is_deleted IS '软删除标记';

COMMENT ON COLUMN comments.created_at IS '创建时间';

COMMENT ON COLUMN comments.updated_at IS '更新时间';

CREATE TABLE post_tags (
    post_id UUID NOT NULL, 
    tag_id UUID NOT NULL, 
    PRIMARY KEY (post_id, tag_id), 
    FOREIGN KEY(post_id) REFERENCES posts (id) ON DELETE CASCADE, 
    FOREIGN KEY(tag_id) REFERENCES tags (id) ON DELETE CASCADE
);

CREATE TABLE post_views (
    id UUID NOT NULL, 
    user_id UUID, 
    post_id UUID NOT NULL, 
    ip_address VARCHAR(45), 
    user_agent VARCHAR(500), 
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(post_id) REFERENCES posts (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

COMMENT ON COLUMN post_views.id IS '浏览记录唯一标识符';

COMMENT ON COLUMN post_views.user_id IS '浏览用户ID（NULL表示匿名用户）';

COMMENT ON COLUMN post_views.post_id IS '被浏览的文章ID';

COMMENT ON COLUMN post_views.ip_address IS '访问者IP地址';

COMMENT ON COLUMN post_views.user_agent IS '浏览器User-Agent信息';

COMMENT ON COLUMN post_views.viewed_at IS '浏览时间';

CREATE INDEX idx_post_viewed ON post_views (post_id, viewed_at);

CREATE INDEX idx_user_viewed ON post_views (user_id, viewed_at);

CREATE INDEX ix_post_views_post_id ON post_views (post_id);

CREATE INDEX ix_post_views_user_id ON post_views (user_id);

CREATE INDEX ix_post_views_viewed_at ON post_views (viewed_at);

INSERT INTO alembic_version (version_num) VALUES ('b9cf7908383e') RETURNING alembic_version.version_num;

COMMIT;

